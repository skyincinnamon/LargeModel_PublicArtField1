import os
import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
    BitsAndBytesConfig,
    EarlyStoppingCallback,
    GenerationConfig
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, PeftModel
import numpy as np
import gc

# ================= 路径配置 ==================
model_path = r"models\Qwen3-8B"
data_path = r"knowledge_base\问答对"
output_dir = r"models\Qwen3-8B-optimized"

# 创建输出目录
os.makedirs(output_dir, exist_ok=True)

# ================= 量化配置 ==================
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
)

# ================= 加载模型和分词器 ==================
print("加载模型和分词器...")
tokenizer = AutoTokenizer.from_pretrained(
    model_path,
    trust_remote_code=True,
    padding_side="right",
    use_fast=False
)
# 设置截断方向为左侧（全局设置）
tokenizer.truncation_side = "left"
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_path,
    trust_remote_code=True,
    quantization_config=bnb_config,
    device_map="auto",
    max_memory={0: "10GB"},
    low_cpu_mem_usage=True,
)
model = prepare_model_for_kbit_training(model)
model.gradient_checkpointing_enable()
model.config.use_cache = False

# ================= LoRA配置优化 ==================
print("配置LoRA...")
lora_config = LoraConfig(
    r=48,  # 平衡模型容量和训练速度
    lora_alpha=96,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# ================= 数据处理优化 ==================
print("加载和处理数据...")
dataset = load_dataset("json", data_files=os.path.join(data_path, "*.json"))["train"]

# 数据过滤和增强
def clean_data(example):
    """过滤无效样本和短样本"""
    if not example['instruction'] or not example['output']:
        return False
    if len(example['output']) < 30:  # 过滤过短回答
        return False
    return True

# 优化提示格式 - 添加明确的角色标识
def format_prompt(example):
    system_prompt = "你是一个公共艺术专家，请用专业且易懂的方式回答以下问题。"
    user_prompt = f"[|im_start|]user\n{example['instruction']}[|im_end|]"
    assistant_prompt = f"[|im_start|]assistant\n{example['output']}[|im_end|]"
    return {"text": f"{system_prompt}\n{user_prompt}{assistant_prompt}"}

# 应用处理
dataset = dataset.filter(clean_data)
dataset = dataset.train_test_split(test_size=0.15, seed=42)
dataset = dataset.map(format_prompt).filter(lambda x: x["text"] is not None)

# ================= 分词函数优化 ==================
def tokenize_function(examples):
    texts = examples["text"]
    # 动态截断 - 保留更多上下文信息
    tokenized = tokenizer(
        texts,
        max_length=512,  # 增加长度获取更多上下文
        truncation=True,
        padding="max_length",
        return_tensors="pt",
    )
    
    input_ids = tokenized["input_ids"]
    attention_mask = tokenized["attention_mask"]
    
    labels = input_ids.clone()
    # 标记非助手部分为-100 (忽略loss计算)
    for i, text in enumerate(texts):
        try:
            # 查找助手文本位置
            assistant_idx = text.find("[|im_start|]assistant")
            if assistant_idx == -1:
                # 未找到则全部标记忽略
                labels[i, :] = -100
                continue
            
            # 计算助手token位置
            prompt_text = text[:assistant_idx]
            prompt_tokens = tokenizer(prompt_text, return_tensors="pt")["input_ids"][0]
            
            # 跳过特殊token
            prompt_tokens = prompt_tokens[prompt_tokens != tokenizer.eos_token_id]
            prompt_tokens = prompt_tokens[prompt_tokens != tokenizer.pad_token_id]
            
            # 设置标签 (仅助手部分计算loss)
            labels[i, :len(prompt_tokens)] = -100
        except Exception as e:
            print(f"标签生成错误: {e}")
            labels[i, :] = -100
    
    tokenized["labels"] = labels
    return tokenized

tokenized_dataset = dataset.map(
    tokenize_function,
    batched=True,
    batch_size=8,  # 减少批大小避免OOM
    remove_columns=dataset["train"].column_names
)

# ================= 训练参数优化 ==================
training_args = TrainingArguments(
    output_dir=output_dir,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=12,  # 平衡内存和更新频率
    num_train_epochs=6,  # 减少训练轮次
    learning_rate=3e-5,  # 优化学习率
    warmup_ratio=0.1,  # 使用预热
    lr_scheduler_type="cosine",  # 简化学习率调度
    logging_steps=10,
    eval_steps=40,  # 更频繁评估
    eval_strategy="steps",
    save_steps=80,
    save_total_limit=3,  # 限制保存点数量
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",  # 使用损失选择最佳模型
    greater_is_better=False,
    weight_decay=0.02,  # 增加权重衰减
    fp16=False,
    bf16=True,
    report_to=["tensorboard"],
    run_name="qwen3-8b-art-specialist",
    remove_unused_columns=False
)

# ================= 训练器配置 ==================
data_collator = DataCollatorForSeq2Seq(
    tokenizer,
    pad_to_multiple_of=8,
    padding=True,
    return_tensors="pt",
    label_pad_token_id=-100
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["test"],
    data_collator=data_collator,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
)

# ================= 训练与保存 ==================
print("开始训练...")
trainer.train()

print("保存模型...")
model.save_pretrained(output_dir)
tokenizer.save_pretrained(output_dir)

# ================= 模型测试函数 ==================
def test_model(model, tokenizer, test_cases):
    """在测试用例上评估模型性能"""
    print("\n" + "="*50)
    print("测试用例生成:")
    
    # 配置生成参数
    generation_config = GenerationConfig(
        max_new_tokens=300,
        temperature=0.7,
        top_p=0.85,
        top_k=50,
        repetition_penalty=1.15,
        do_sample=True,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id
    )
    
    model.eval()
    with torch.no_grad():
        for q in test_cases:
            # 修复输入格式问题
            prompt = f"[|im_start|]user\n{q}[|im_end|]\n[|im_start|]assistant\n"
            
            # 仅使用input_ids确保格式正确
            inputs = tokenizer(
                prompt,
                return_tensors="pt", 
                padding=True, 
                truncation=True, 
                max_length=256
            )
            
            # 显式指定input_ids作为输入
            outputs = model.generate(
                input_ids=inputs["input_ids"].to(model.device),
                attention_mask=inputs["attention_mask"].to(model.device),
                generation_config=generation_config
            )
            
            # 解码并清理响应
            full_response = tokenizer.decode(outputs[0], skip_special_tokens=False)
            
            # 提取助手回答
            if "[|im_start|]assistant" in full_response:
                response = full_response.split("[|im_start|]assistant")[-1]
                response = response.replace("[|im_end|]", "").split("]")[0].strip()
            else:
                response = full_response
            
            print(f"\n问题：{q}")
            print(f"回答：{response}")
            print("-"*50)
    
    # 内存清理
    del model
    torch.cuda.empty_cache()
    gc.collect()

# ================= 主执行流程 ==================
print("\n训练结束，开始测试...")
art_test_cases = [
    "公共艺术如何塑造城市identity？",
    "如何评价当代公共艺术中的社区参与式创作？",
    "传统雕塑与数字媒体艺术在公共空间中的互动关系是什么？",
    "公共艺术项目的社会投资回报率如何量化？"
]

test_model(model, tokenizer, art_test_cases)  # 使用训练好的模型直接测试

print("保存模型...")
model.save_pretrained(output_dir)
tokenizer.save_pretrained(output_dir)

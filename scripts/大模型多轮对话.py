import torch
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM
import os

# 设置日志配置
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
transformers_logger = logging.getLogger('transformers')
transformers_logger.setLevel(logging.INFO)

# 加载微调后的模型和分词器
model_path = r"models\Qwen3-8B-optimized"  # 微调后的模型路径
tokenizer = AutoTokenizer.from_pretrained(
    model_path,
    trust_remote_code=True,
    padding_side="right",
    use_fast=False
)
tokenizer.truncation_side = "left"
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_path,
    trust_remote_code=True,
    device_map="auto",
    torch_dtype=torch.bfloat16
)
model.eval()  # 设置为评估模式

logging.info("模型和分词器已加载到设备：%s", model.device)

def chat_with_history(messages):
    """
    输入: messages为历史消息列表（格式同原脚本）
    输出: 模型回复文本
    """
    def build_chat_history(messages):
        chat_history = ""
        system_prompt = ""
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
                break
        if system_prompt:
            chat_history += f"你是一个公共艺术专家，请用专业且易懂的方式详细回答以下问题，提供丰富的信息和例子。\n"
        for i, msg in enumerate(messages):
            if msg["role"] == "user":
                chat_history += f"[|im_start|]user\n{msg['content']}[|im_end|]\n"
            elif msg["role"] == "assistant" and i > 0:
                chat_history += f"[|im_start|]assistant\n{msg['content']}[|im_end|]\n"
        if messages[-1]["role"] == "user":
            chat_history += f"[|im_start|]user\n{messages[-1]['content']}[|im_end|]\n[|im_start|]assistant\n"
        return chat_history

    chat_history = build_chat_history(messages)
    input_ids = tokenizer(
        chat_history,
        return_tensors="pt",
        max_length=512,
        truncation=True
    ).input_ids.to(model.device)
    generation_config = {
        "max_new_tokens": 500,
        "temperature": 0.8,
        "top_p": 0.9,
        "top_k": 50,
        "repetition_penalty": 1.15,
        "do_sample": True,
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id
    }
    with torch.no_grad():
        outputs = model.generate(
            input_ids=input_ids,
            **generation_config
        )
    full_response = tokenizer.decode(outputs[0], skip_special_tokens=False)
    if "[|im_start|]assistant" in full_response:
        response = full_response.split("[|im_start|]assistant")[-1]
        special_tokens = ["[|im_end|]", "<|im_end|>", "]", "|im_end|", "<|im_start|>", "|im_start|"]
        for token in special_tokens:
            response = response.split(token)[0].strip()
        response = response.strip()
    else:
        response = full_response
    return response

# 多轮会话循环
if __name__ == "__main__":
    messages = [
        {
            "role": "system",
            "content": "你是一个公共艺术专家，请用专业且易懂的方式详细回答以下问题，提供丰富的信息和例子。"
        }
    ]
    while True:
        user_input = input("用户：")
        if user_input.lower() in ['退出', 'exit', 'quit']:
            print("结束对话。")
            break
        messages.append({
            "role": "user",
            "content": user_input
        })
        response = chat_with_history(messages)
        print("助手：" + response)
        messages.append({
            "role": "assistant",
            "content": response.strip()
        })
        max_history = 5
        if len(messages) > max_history * 2 + 1:
            messages = [messages[0]] + messages[-max_history*2:]
            logging.info("消息列表已截断，保留最近的 %d 轮对话。", max_history)
        torch.cuda.empty_cache()
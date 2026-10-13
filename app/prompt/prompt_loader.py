from pathlib import Path


def load_prompt(name:str)->str:

    # 定义路径
    prompt_path=Path(__file__).parents[2]/'prompts'/f"{name}.prompt"
    # 加载内容
    return prompt_path.read_text(encoding="utf-8")

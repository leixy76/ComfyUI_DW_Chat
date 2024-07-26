import os
import json
from openai import OpenAI

def get_moonshot_api_key():
    try:
        config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')
        with open(config_path, 'r') as f:  
            config = json.load(f)
        api_key = config["MOONSHOT_API_KEY"]
    except:
        print("出错啦 Error: API key is required")
        return ""
    return api_key

class MoonshotChatBaseNode:
    def __init__(self):
        self.client = None
        self.api_key = get_moonshot_api_key()
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url="https://api.moonshot.cn/v1")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "model": (["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],),
                "temperature": ("FLOAT", {"default": 0.3, "min": 0.0, "max": 2.0, "step": 0.1}),
                "max_tokens": ("INT", {"default": 1000, "min": 1, "max": 128000}),
            },
            "optional": {
                "system_message": ("STRING", {"multiline": True}),
            }
        }

    RETURN_TYPES = ("STRING",)

class MoonshotSingleChatNode(MoonshotChatBaseNode):
    FUNCTION = "generate_single_response"
    RETURN_NAMES = ("response",)

    def generate_single_response(self, prompt, model, temperature, max_tokens, system_message=""):
        if not self.client:
            return ("Error: MOONSHOT_API_KEY not set or invalid. Please check your config.json file.",)

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return (completion.choices[0].message.content,)
        except Exception as e:
            return (f"Error: {str(e)}",)

class MoonshotMultiChatNode(MoonshotChatBaseNode):
    FUNCTION = "generate_chat"
    RETURN_NAMES = ("chat_history",)
    CATEGORY = "🌙DW/moonshotChat"
    
    def __init__(self):
        super().__init__()
        self.conversation_history = []

    @classmethod
    def INPUT_TYPES(cls):
        input_types = super().INPUT_TYPES()
        input_types["optional"]["reset_conversation"] = ("BOOLEAN", {"default": False})
        return input_types

    def generate_chat(self, prompt, model, temperature, max_tokens, system_message="", reset_conversation=False):
        if not self.client:
            return ("Error: MOONSHOT_API_KEY not set or invalid. Please check your config.json file.",)

        if reset_conversation:
            self.conversation_history = []

        if not self.conversation_history and system_message:
            self.conversation_history.append({"role": "system", "content": system_message})

        self.conversation_history.append({"role": "user", "content": prompt})

        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=self.conversation_history,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            response = completion.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": response})
            chat_history = self.format_chat_history()
            return (chat_history,)
        except Exception as e:
            return (f"Error: {str(e)}",)

    def format_chat_history(self):
        formatted_history = []
        for message in self.conversation_history:
            formatted_message = f"{message['role']}: {message['content']}"
            formatted_history.append(formatted_message)
            formatted_history.append("-" * 40)  # 添加分隔线
        return "\n".join(formatted_history)

NODE_CLASS_MAPPINGS = {
    "MoonshotSingleChatNode": MoonshotSingleChatNode,
    "MoonshotMultiChatNode": MoonshotMultiChatNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MoonshotSingleChatNode": "🌙Moonshot Single Chat",
    "MoonshotMultiChatNode": "🌙Moonshot Multi Chat"
}
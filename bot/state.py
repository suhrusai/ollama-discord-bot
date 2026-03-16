from bot.config import DEFAULT_MODEL

chat_history = {}
user_models = {}

def get_user_model(user_id: str):
    return user_models.get(user_id, DEFAULT_MODEL)

def set_user_model(user_id: str, model: str):
    user_models[user_id] = model

def reset_user_state(user_id: str):
    user_models.pop(user_id, None)
    chat_history.pop(user_id, None)

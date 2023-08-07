from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import ChatMessage
from langchain.prompts.chat import (
    SystemMessagePromptTemplate,
)
import streamlit as st
import random
import time
from typing import Dict, TypedDict
import re
import os

#  Custom select component
from avatarselect import avatarselect

"""
# 👨‍👩‍👧‍👦 GroupChatGPT

"""


HOST = "https://groupchatgpt.streamlit.app"


class Character(TypedDict):
    value: str
    display_name: str
    avatar: str


CHARACTERS: Dict[str, Character] = {
    "rick": {
        "value": "rick",
        "display_name": "Rick Sanchez",
        "avatar": "https://i.imgur.com/LwYm9Jk.png",
    },
    "barbie": {
        "value": "barbie",
        "display_name": "Barbie",
        "avatar": "https://i.imgur.com/tyJajYs.png",
    },
    "yoda": {
        "value": "yoda",
        "display_name": "Yoda",
        "avatar": "https://i.imgur.com/z29bSou.png",
    },
    "cartman": {
        "value": "cartman",
        "display_name": "Eric Cartman",
        "avatar": "https://i.imgur.com/MSEbuEU.png",
    },
    "stewie": {
        "value": "stewie",
        "display_name": "Stewie Griffin",
        "avatar": "https://i.imgur.com/zIwZH3q.png",
    },
    "batman": {
        "value": "batman",
        "display_name": "Batman",
        "avatar": "https://i.imgur.com/kTtbJLJ.png",
    },
    "morty": {
        "value": "morty",
        "display_name": "Morty",
        "avatar": "https://i.imgur.com/QMqm5rC.png",
    },
    "spongebob": {
        "value": "spongebob",
        "display_name": "Spongebob Squarepants",
        "avatar": "https://i.imgur.com/i6O9v2H.png",
    },
    "ken": {
        "value": "ken",
        "display_name": "Ken Doll",
        "avatar": "https://i.imgur.com/ENnWII9.png",
    },
    "pooh": {
        "value": "pooh",
        "display_name": "Winnie the Pooh",
        "avatar": "https://i.imgur.com/WL5hhce.png",
    },
    "oppenheimer": {
        "value": "oppenheimer",
        "display_name": "Robert Oppenheimer",
        "avatar": "https://i.imgur.com/qVYBzk4.png",
    },
}

from supabase import create_client


# Initialize DB connection on app load
@st.cache_resource
def init_connection():
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_key"]

    return create_client(url, key)


supabase = init_connection()

st.markdown(
    """
<style>
    div[data-testid="toastContainer"] {
        z-index: 999992;
    }
    div[data-testid="stToast"] {
        border: 2px solid rgb(0, 66, 128);
        width: 100%;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Example: https://groupchatgpt.streamlit.io/?chat=123
qp = st.experimental_get_query_params()
url_chat_id = qp.get("chat", [None])[0]

RENDER_READONLY = bool(url_chat_id)

if url_chat_id:
    data, _ = (
        supabase.table("messages")
        .select("*")
        .eq("chat_id", url_chat_id)
        .order("order")
        .execute()
    )

    st.session_state["messages"] = [
        ChatMessage(
            role="user",
            content=msg["content"],
            additional_kwargs={
                "character": CHARACTERS[msg["character"]]
                if msg["character"] != "user"
                else {}
            },
        )
        for msg in data[1]
    ]

    st.session_state["chat_id"] = url_chat_id


if not st.session_state.get("has_started_conversation"):
    st.session_state["chosen_characters"] = {}


if not RENDER_READONLY:
    if not st.session_state.get("has_started_conversation"):
        st.info(
            "Choose your friends! Then start by asking a question or just saying hi!"
        )
        avatarselect_placeholder = st.empty()
        with avatarselect_placeholder:
            chosen_character_values = avatarselect(CHARACTERS)

            if chosen_character_values:
                for value in chosen_character_values:
                    st.session_state.chosen_characters[value] = CHARACTERS[value]
    else:
        avatarselect_placeholder = st.empty()


def get_response_prefix(text):
    """
    Rick Sanchez: lorem ipsum -> Rick Sanchez
    Winnie the Pooh: lorem ipsum -> Winnie the Pooh
    lorem ipsum -> None
    """
    pattern = r"^\s*([\w\s]+(?=:))"
    match = re.match(pattern, text)
    if match:
        return match.group(1).strip()
    else:
        return None


def replace_prefix(text, character):
    _text = text

    prefix = get_response_prefix(_text)
    if not prefix:
        return _text

    if (
        prefix == character.get("display_name")
        or prefix in character.get("display_name", "").split(" ")
        or prefix == "Friend"
    ):
        _text = _text.replace(prefix + ":", "")

    return _text


class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, character, initial_text=""):
        self.character = character
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token

        self.text = replace_prefix(self.text, self.character)

        # This is to avoid showing the prefix in the partial stream
        if len(self.text) < len(self.character["display_name"]) + 2:
            return

        self.container.markdown(self.text)


def share_conversation():
    chat_id = st.session_state.get("chat_id")
    if chat_id:
        # Replace existing chat
        supabase.table("chats").delete().eq("id", chat_id).execute()
        data, _ = supabase.table("chats").insert({"id": chat_id}).execute()
    else:
        # Create new chat
        data, _ = supabase.table("chats").insert({}).execute()

    chat_id = str(data[1][0]["id"])
    st.session_state["chat_id"] = chat_id

    for count, msg in enumerate(st.session_state.messages):
        character = msg.additional_kwargs.get("character", {})

        data, _ = (
            supabase.table("messages")
            .insert(
                {
                    "chat_id": chat_id,
                    "content": msg.content,
                    "character": character.get("value", "user"),
                    "order": count,
                }
            )
            .execute()
        )

    st.toast(f"Share link: {HOST}?chat=" + str(chat_id), icon="🔗")


if not RENDER_READONLY:
    with st.sidebar:
        if os.getenv("STREAMLIT_LOCAL"):
            openai_api_key = os.getenv("OPEN_AI_KEY")
            st.text_input("Using Env OpenAI API Key", disabled=True)
        else:
            openai_api_key = st.text_input("OpenAI API Key", type="password")
        st.button("Share conversation", on_click=share_conversation)
else:
    with st.sidebar:

        def new_conversation():
            st.session_state["chat_id"] = None
            st.session_state["messages"] = []
            st.experimental_set_query_params()

        def fork_conversation():
            st.session_state["chat_id"] = None
            st.experimental_set_query_params()

        st.button("Start new chat", on_click=new_conversation, use_container_width=True)
        st.button("Fork chat", on_click=fork_conversation, use_container_width=True)

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state.messages:
    character = msg.additional_kwargs.get("character", {})
    value = character.get("value", "user")
    avatar = character.get("avatar", None)

    content = replace_prefix(msg.content, character)

    st.chat_message(
        value,
        avatar=avatar,
    ).write(content)


CHARACTER_PROMPT_TEMPLATE = """You are {display_name}. Do not go off character.
Do not start the message with your name. Always respond as if you are {display_name}.
You are in a group setting, so please make sure to be conversational. Lean into your personality and perspective as much as possible.
Keep your responses under 60 words please."""

RETORT_PROMPT = "Make a critical comment about the last thing the chat said and follow up with an interesting question that spices up the conversation."


def get_number_of_bot_responses(*, prompt=""):
    # If there is only one character, they can't talk with themselves!
    if len(st.session_state.chosen_characters.keys()) < 2:
        return 1

    return (len(prompt) % 2) * 2 + 3


def get_character_system_message(*, character: Character):
    character_prompt_template = SystemMessagePromptTemplate.from_template(
        template=CHARACTER_PROMPT_TEMPLATE
    )
    return character_prompt_template.format(display_name=character["display_name"])


def pick_character(*, exclude=[]) -> Character:
    character_list = [
        x for x in list(st.session_state.chosen_characters.keys()) if x not in exclude
    ]
    key = random.choice(character_list)
    return st.session_state.chosen_characters[key]


def reduce_messages_below_token_limit(llm, messages):
    buffer = messages.copy()
    curr_buffer_length = llm.get_num_tokens_from_messages(messages)
    max_token_limit = 3000
    while curr_buffer_length > max_token_limit and len(buffer) > 0:
        buffer = buffer[1:]
        curr_buffer_length = llm.get_num_tokens_from_messages(buffer)

    return buffer


if not RENDER_READONLY:
    if prompt := st.chat_input():
        if not openai_api_key:
            st.warning("Please add your OpenAI API key to continue.")
            st.stop()

        if len(st.session_state.chosen_characters.keys()) == 0:
            st.warning("Please select at least one character to continue.")
            st.stop()

        st.session_state["has_started_conversation"] = True
        avatarselect_placeholder.empty()

        st.session_state.messages.append(
            ChatMessage(role="user", content=f"Friend: {prompt}")
        )
        st.chat_message("user").write(prompt)

        number_of_bot_responses = get_number_of_bot_responses(prompt=prompt)

        for i in range(number_of_bot_responses):
            previous_character = (
                st.session_state.messages[-1]
                .additional_kwargs.get("character", {})
                .get("value")
            )
            character = pick_character(exclude=[previous_character])
            system_message = get_character_system_message(character=character)

            if i % 2 == 1:
                system_message.content = system_message.content + " " + RETORT_PROMPT

            messages = [system_message] + reduce_messages_below_token_limit(
                ChatOpenAI(openai_api_key=openai_api_key), st.session_state.messages
            )

            with st.chat_message(
                character["value"], avatar=character.get("avatar", None)
            ):
                with st.spinner(""):
                    time.sleep(2)

                stream_handler = StreamHandler(st.empty(), character)
                llm = ChatOpenAI(
                    openai_api_key=openai_api_key,
                    streaming=True,
                    callbacks=[stream_handler],
                )

                response = llm(messages)

                answer = replace_prefix(response.content, character)

                st.session_state.messages.append(
                    ChatMessage(
                        role="user",
                        content=f"{character['display_name']}: {answer}",
                        additional_kwargs={"character": character},
                    )
                )

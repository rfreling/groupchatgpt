import os
import streamlit.components.v1 as components

_USE_WEB_DEV_SERVER = os.getenv("STREAMLIT_LOCAL")

if _USE_WEB_DEV_SERVER:
    _component_func = components.declare_component(
        "avatarselect", url="http://localhost:3001"
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("avatarselect", path=build_dir)


def avatarselect(characters):
    component_value = _component_func(characters=characters, default=None)
    return component_value

import nltk
import io
import contextlib

def show_usage(obj:object) -> str:
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):

        nltk.usage(obj)
        return buf.getvalue()

# --- test ---

assert "LazyModule supports the following operations" in show_usage(nltk.corpus)

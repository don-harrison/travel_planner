import requests
import wikipedia

def get_wikipedia_content(title, language="en"):
    try:
        wikipedia.set_lang(language)
        page = wikipedia.page(title)
        return {
            "title": page.title,
            "content": page.content,
            "url": page.url
        }
    except wikipedia.exceptions.DisambiguationError as e:
        return{"error": f"Disambiguation error: {e.options}"}
    except wikipedia.exceptions.PageError:
        return {"error": "Page not found"}
    except Exception as e:
        return {"error": str(e)}
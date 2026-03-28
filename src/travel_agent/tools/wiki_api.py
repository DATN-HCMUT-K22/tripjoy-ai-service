import wikipediaapi
from ..models.models import TravelNotebook

def find_section_recursive(sections, keywords):

    for sec in sections:
        title = sec.title.lower().strip()

        for kw in keywords:
            if kw.lower() == title:
                if sec.text.strip():
                    return sec.text

    for sec in sections:
        title = sec.title.lower()

        for kw in keywords:
            if kw.lower() in title:
                if sec.text.strip():
                    return sec.text

        # recursion
        result = find_section_recursive(sec.sections, keywords)
        if result:
            return result

    return None

def get_destination_info(location: str):
    def fetch_from_wiki(language: str):
        wiki = wikipediaapi.Wikipedia(
            user_agent="tripjoy (your_email@example.com)",
            language=language,
        )

        page = wiki.page(location)

        if not page.exists():
            return None

        # FOOD
        food_keywords = ["Ẩm thực", "Đặc sản ẩm thực", "Food"]
        food = find_section_recursive(page.sections, food_keywords)

        # CLIMATE
        climate_titles = [
            "Khí hậu", "Khí hậu và thời tiết",
            "Climate", "Climate and weather"
        ]
        climate = next(
            (sec.text for title in climate_titles if (sec := page.section_by_title(title))),
            ""
        )

        # CULTURE
        culture_titles = [
            "Văn hóa", "Văn hoá",
            "Culture", "Culture and society",
            "Xã hội", "Đời sống"
        ]
        culture = next(
            (sec.text for title in culture_titles if (sec := page.section_by_title(title))),
            ""
        )

        return {
            "food": food or "",
            "climate": climate or "",
            "culture": culture or ""
        }

    # Ưu tiên tiếng Việt
    result_vi = fetch_from_wiki("vi")

    # Nếu thiếu dữ liệu thì fallback tiếng Anh
    if not result_vi or (not result_vi["climate"] and not result_vi["culture"]):
        result_en = fetch_from_wiki("en")

        if result_en:
            return {
                "food": (result_vi["food"] if result_vi else "") or result_en["food"],
                "climate": (result_vi["climate"] if result_vi else "") or result_en["climate"],
                "culture": (result_vi["culture"] if result_vi else "") or result_en["culture"],
            }

    # Nếu có data tiếng Việt
    if result_vi:
        return result_vi

    # fallback cuối cùng
    return {
        "food": "",
        "climate": "",
        "culture": ""
    }

if __name__ == "__main__":

    result = get_destination_info("Đà Lạt")

    print("\n--- FOOD ---")
    print(result.food)

    print("\n--- CLIMATE ---")
    print(result.climate)

    print("\n--- CULTURE ---")
    print(result.culture)

    print("\n" + "-" * 80)

import requests

def get_address_from_slug(slug):
    url = f"https://thedyrt.com/api/v6/campgrounds?filter[search][slug]={slug}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json().get("data", [])
        if data:
            attrs = data[0].get("attributes", {})
            return {
                "address":     attrs.get("address"),
                "city":        attrs.get("city"),
                "region":      attrs.get("region"),
                "postal_code": attrs.get("postal-code")
            }
    except Exception as e:
        print(f"Could not fetch address for slug '{slug}': {e}")
    return None

adres = get_address_from_slug("utah-watchman")
if adres != None:
    print(str(adres))
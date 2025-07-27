import json







with open("app/store/dive-sites.json", "r") as f:
    data = json.load(f)


class DiveSiteService:
    def get_dive_sites(self):
        return data


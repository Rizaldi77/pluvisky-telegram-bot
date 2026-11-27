import pendulum
import re
import sys

from datetime import datetime
from bs4 import BeautifulSoup
from pluvisky.constants.date_constant import MONTH
from pluvisky.clients.bmkg_clients import BmkgClients


class BmkgService: 
    def __init__(self):
        self.__table_selector = (
            "#__nuxt > main > div.bg-white > div > "
            "div.relative.mt-6.overflow-x-hidden.md\\:mt-10 > "
            "div.overflow-x-auto > div > table"
        )
        self.__month: dict = MONTH
        self.__local_tz = pendulum.timezone(name="Asia/Jakarta")
        self.__date_re = re.compile(r"^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$")
        self.__hours_re = re.compile(r"^(\d{1,2})[.:](\d{2})$")
        self.__section_titles: dict = {"cuaca, suhu, kelembapan", "angin", "jarak pandang"}
        self.__wind_directions: dict = {
            "utara", 
            "timur laut", 
            "timur", 
            "tenggara",
            "selatan", 
            "barat daya", 
            "barat", 
            "barat laut",
        }
        self.__bmkg_clients: BmkgClients = BmkgClients()

    def __classify(self, values: list): 
        sample = next((val for val in values if val), "")
        if not sample:
            return None
        if "°" in sample:
            return "suhu_c"
        if sample.endswith("%"):
            return "kelembapan_persen"
        if "km/j" in sample:
            return "kecepatan_angin_kmh"
        if sample.lower() in self.__wind_directions:
            return "arah_angin"
        if sample == "-" or "km" in sample:
            return "jarak_pandang"
        return "cuaca"

    def __clean(self, text: str) -> str: 
        return " ".join(text.split())

    def __to_number(self, text: str): 
        value = re.search(r"-?\d+(?:[.,]\d+)?", text or "")
        if not value:
            return None
        num = float(value.group().replace(",", "."))
        return int(num) if num.is_integer() else num

    def __parse_date(self, text: str) -> str: 
        day, month, year = self.__date_re.match(text).groups()
        return f"{int(year):04d}-{self.__month[month.lower()[:3]]:02d}-{int(day):02d}"

    def __expand_row(self, table_tr) -> list[str]: 
        values = []
        for cell in table_tr.find_all(["td", "th"], recursive=False): 
            try:
                span = int(cell.get("colspan", 1))
            except ValueError: 
                span = 1
            values.extend([self.__clean(cell.get_text(" "))] * max(span, 1))
        return values

    def __get_parse(self, rows, kind, tot_hours, i):
        return rows.get(kind, [""] * tot_hours)[i]

    def __parse_table(self, table) -> list: 
        dates: list = []
        hours: list = []
        rows: dict = {}

        for tr in table.find_all("tr"): 
            cells = tr.find_all(["td", "th"], recursive=False)
            texts = [self.__clean(c.get_text(" ")) for c in cells]

            date_cells = [t for t in texts if self.__date_re.match(t)]
            if date_cells: 
                if not dates:
                    dates = date_cells
                continue

            values = self.__expand_row(tr)
            non_empty = [v for v in values if v]
            if not non_empty:
                continue
    
            if all(self.__hours_re.match(v) for v in non_empty):
                if not hours:
                    hours = values
                continue
    
            if len(texts) == 1 and texts[0].lower() in self.__section_titles:
                continue
    
            kind = self.__classify(values)
            if kind and kind not in rows:
                rows[kind] = values

        if not dates or not hours:
                raise ValueError("Baris tanggal/jam tidak ditemukan di tabel.")

        tot_hours = len(hours)
        for kind, vals in rows.items():
            if len(vals) != tot_hours:
                print(
                    f"[peringatan] baris '{kind}' berisi {len(vals)} sel, "
                    f"jam berisi {tot_hours}; disesuaikan.",
                    file=sys.stderr,
                )
                rows[kind] = (vals + [""] * tot_hours)[:tot_hours]

        records = []
        date_idx, prev_hour = 0, -1
        for i, jam in enumerate(hours):
            h, m = map(int, self.__hours_re.match(jam).groups())
            if h < prev_hour:  # lewat tengah malam -> tanggal berikutnya
                date_idx += 1
            prev_hour = h
            tanggal = self.__parse_date(dates[min(date_idx, len(dates) - 1)])
    
            jarak = self.__get_parse(rows, "jarak_pandang", tot_hours, i)
            records.append({
                "date": tanggal,
                "hours": f"{h:02d}:{m:02d}",
                "datetime": f"{tanggal}T{h:02d}:{m:02d}:00+07:00",
                "weather": self.__get_parse(rows, "cuaca", tot_hours, i) or None,
                "temperature_c": self.__to_number(self.__get_parse(rows, "suhu_c", tot_hours, i)),
                "humidity_percent": self.__to_number(self.__get_parse(rows, "kelembapan_persen", tot_hours, i)),
                "wind_velocity_kmh": self.__to_number(self.__get_parse(rows, "kecepatan_angin_kmh", tot_hours, i)),
                "wind_direction": self.__get_parse(rows, "arah_angin", tot_hours, i) or None,
                "visibility": None if jarak in ("", "-") else jarak,
            })
        return records

    def __parse_metadata(self, url: str, subdistrict_code: str, soup: BeautifulSoup) -> dict: 
        
        h1 = soup.select_one("h1")
        location = self.__clean(h1.get_text()) if h1 else None
        
        if location: 
            location = re.sub(r"^Prakiraan Cuaca\s+", "", location)

        area = soup.find(string=re.compile(r"^\s*Prakiraan cuaca di "))
        page_text = soup.get_text("\n")
        latest_update = re.search(r"Prakiraan per Jam.*?Pemutakhiran:\s*([^\n]+)", page_text, re.S)

        return {
            "subdistrict_code": subdistrict_code,
            "location": location,
            "area": self.__clean(area) if area else None,
            "updated_at": self.__clean(latest_update.group(1)) if latest_update else None,
            "source": url, 
            "crawled_at": datetime.now(tz=self.__local_tz).isoformat(timespec="seconds")
        }

    def get_data_forecast(self, subdistrict_code: str): 
        resp_html = self.__bmkg_clients.get_bmkg_forecast(subdistrict_code)
        soup = BeautifulSoup(resp_html["results"], "lxml")

        table = soup.select_one(self.__table_selector) or soup.find("table")
        if table is None: 
            return {"error": "Failed to get data table"}

        records = self.__parse_table(table)
        return {
            **self.__parse_metadata(resp_html['url'], subdistrict_code, soup), 
            "total_data": len(records), 
            "data": records
        }



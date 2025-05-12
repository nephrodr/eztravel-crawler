from flask import Flask, render_template, request, make_response
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
from io import BytesIO
import pandas as pd
import os
import time

app = Flask(__name__)

city_code_dict = {
    '台北': 'tpe', '松山': 'tsa', '台中': 'rmq', '嘉義': 'cyi', '台南': 'tnn',
    '高雄': 'khh', '花蓮': 'hun', '台東': 'ttt', '澎湖': 'mzg', '金門': 'knh',
    '東京': 'tyo', '大阪': 'osa', '福岡': 'fuk', '名古屋': 'ngo', '廣島': 'hij',
    '仙台': 'sdj', '花卷': 'hna', '熊本': 'kmj', '函館': 'hkd', '札幌': 'spk',
    '沖繩': 'oka', '首爾': 'sel', '釜山': 'pus', '高松': 'tak', '濟州島': 'cju'
}

def create_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)

def fetch_elements(driver, selector, limit=5):
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        return [element.text or None for element in elements[:limit]] if elements else [None] * limit
    except:
        return [None] * limit

def crawl_flight_data(dep_code, dest_code, start_date, end_date, days):
    url_template = f"https://flight.eztravel.com.tw/tickets-roundtrip-{dep_code}-{dest_code}/?outbounddate={{}}&inbounddate={{}}"
    driver = create_driver()
    data = []

    for offset in range((end_date - start_date).days + 1):
        outbound = (start_date + timedelta(days=offset)).strftime("%d/%m/%Y").replace('/', '%2F')
        inbound = (start_date + timedelta(days=offset + days - 1)).strftime("%d/%m/%Y").replace('/', '%2F')
        url = url_template.format(outbound, inbound)
        driver.get(url)
        time.sleep(15)

        airlines = fetch_elements(driver, ".v-ellipsis.el-popover__reference")
        departures = fetch_elements(driver, ".departure-sec .time-detail")
        arrivals = fetch_elements(driver, ".arrival-sec .time-detail")
        prices = fetch_elements(driver, ".flight-price .price-top .amount")

        for i in range(min(len(airlines), len(departures), len(arrivals), len(prices))):
            data.append({
                '出發日期': (start_date + timedelta(days=offset)).strftime("%Y/%m/%d"),
                '回程日期': (start_date + timedelta(days=offset + days - 1)).strftime("%Y/%m/%d"),
                '航空公司': airlines[i],
                '起飛時間': departures[i],
                '抵達時間': arrivals[i],
                '價格': prices[i]
            })

    driver.quit()
    return pd.DataFrame(data)

@app.route("/")
def home():
    dep = ['台北', '松山', '台中', '嘉義', '台南', '高雄', '花蓮', '台東',
           '東京', '大阪', '福岡', '名古屋', '廣島', '仙台', '花卷', '熊本', '函館', '札幌',
           '沖繩', '首爾', '釜山', '高松', '濟州島', '澎湖', '金門']
    dest = ['東京', '大阪', '福岡', '名古屋', '廣島', '仙台', '花卷', '熊本', '函館', '札幌',
            '沖繩', '首爾', '釜山', '高松', '濟州島', '澎湖', '金門', '台北', '松山', '台中', '嘉義', '台南', '高雄', '花蓮', '台東']
    return render_template("index.html", departures=dep, destinations=dest)

@app.route("/download", methods=["POST"])
def download():
    dep = request.json['departure']
    dest = request.json['destination']
    start_date = datetime.strptime(request.json['start_date'], "%Y-%m-%d")
    end_date = datetime.strptime(request.json['end_date'], "%Y-%m-%d")
    days = int(request.json['days'])

    dep_code = city_code_dict.get(dep)
    dest_code = city_code_dict.get(dest)
    df = crawl_flight_data(dep_code, dest_code, start_date, end_date, days)

    buffer = BytesIO()
    df.to_csv(buffer, index=False, encoding="utf-8-sig")
    buffer.seek(0)

    response = make_response(buffer.read())
    response.headers.set("Content-Disposition", "attachment; filename=flight_result.csv")
    response.headers.set("Content-Type", "text/csv")
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"✅ Flask server starting on port {port}...")
    app.run(host="0.0.0.0", port=port)

from flask import Flask, render_template, request, make_response, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
from io import BytesIO
import pandas as pd
import os
import time

app = Flask(__name__)

# 城市代碼對照
city_code_dict = {
    '台北': 'tpe', '松山': 'tsa', '台中': 'rmq', '嘉義': 'cyi', '台南': 'tnn',
    '高雄': 'khh', '花蓮': 'hun', '台東': 'ttt', '澎湖': 'mzg', '金門': 'knh',
    '東京': 'tyo', '大阪': 'osa', '福岡': 'fuk', '名古屋': 'ngo', '廣島': 'hij',
    '仙台': 'sdj', '花卷': 'hna', '熊本': 'kmj', '函館': 'hkd', '札幌': 'spk',
    '沖繩': 'oka', '首爾': 'sel', '釜山': 'pus', '高松': 'tak', '濟州島': 'cju'
}

# Selenium 抓取工具

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
    url_template = f"https://flight.eztravel.com.tw/tickets-roundtrip-{dep_code}-{dest_code}/?outbounddate={{}}&inbounddate={{}}&dport=&aport=&adults=1&children=0&infants=0&direct=false&cabintype=any&airline="
    driver = create_driver()
    data = []

    for day_offset in range((end_date - start_date).days + 1):
        outbound_date = (start_date + timedelta(days=day_offset)).strftime("%d/%m/%Y").replace('/', '%2F')
        inbound_date = (start_date + timedelta(days=day_offset + days - 1)).strftime("%d/%m/%Y").replace('/', '%2F')
        url = url_template.format(outbound_date, inbound_date)
        driver.get(url)
        time.sleep(15)

        airline_data = fetch_elements(driver, ".v-ellipsis.el-popover__reference")
        departure_times = fetch_elements(driver, ".departure-sec .time-detail")
        arrival_times = fetch_elements(driver, ".arrival-sec .time-detail")
        prices = fetch_elements(driver, ".flight-price .price-top .amount")

        for i in range(min(len(airline_data), len(departure_times), len(arrival_times), len(prices))):
            data.append({
                '出發日期': (start_date + timedelta(days=day_offset)).strftime("%Y/%m/%d"),
                '回程日期': (start_date + timedelta(days=day_offset + days - 1)).strftime("%Y/%m/%d"),
                '航空公司': airline_data[i],
                '起飛時間': departure_times[i],
                '抵達時間': arrival_times[i],
                '價格': prices[i]
            })

    driver.quit()
    return pd.DataFrame(data)

# 路由：首頁
@app.route("/")
def home():
    departure_cities = [
        '台北', '松山', '台中', '嘉義', '台南', '高雄', '花蓮', '台東',
        '東京', '大阪', '福岡', '名古屋', '廣島', '仙台', '花卷', '熊本', '函館', '札幌',
        '沖繩', '首爾', '釜山', '高松', '濟州島', '澎湖', '金門'
    ]
    destination_cities = [
        '東京', '大阪', '福岡', '名古屋', '廣島', '仙台', '花卷', '熊本', '函館', '札幌',
        '沖繩', '首爾', '釜山', '高松', '濟州島', '澎湖', '金門', '台北', '松山', '台中', '嘉義', '台南', '高雄', '花蓮', '台東'
    ]
    return render_template("index.html", departures=departure_cities, destinations=destination_cities)

# 路由：下載 CSV Blob
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
    app.run(debug=True, port=5000)

from utils.crawler_utils import get_html_data


def get_sector_list():
    urls = get_child_urls("https://finance.vietstock.vn/chi-so-nganh.htm")
    for url in urls:
        if '/nganh/' in url:
            sector = url.split("/")[-1].split('.')[0]
            # print(sector)
            df = get_url_data(url)
            df = df.drop(df.columns[[0, 3, 4, 5, 6]], axis=1)
            df['sector'] = sector
            pd.set_option('display.max_rows', df.shape[0] + 1)
            print(df)


def get_fundamental_data(ticker):
    url = f"https://finance.vietstock.vn/{ticker}/tai-chinh.htm"
    text = get_html_data(url)
    if text.count("Đang bị cảnh báo") > 0:
        return None
    # get relevant content
    text = text.split("Cổ tức TM")[1].split("* EPS theo công bố")[0]
    text = text.replace('T/S cổ tức', '\nT/S cổ tức ')
    text = text.replace('Beta', '\nBeta ')
    text = text.replace('EPS', '\nEPS ')
    text = text.replace('P/E', '\nP/E ', 1)
    text = text.replace('F P/E', '\nF P/E ')
    text = text.replace('BVPS', '\nBVPS ')
    text = text.replace('P/B', '\nP/B ')
    if text.count("-") > 2:
        return None
    else:
        eps = 0
        pe = 0
        attributes = text.splitlines()
        for a in attributes:
            if a.count('EPS') > 0:
                eps = int(a.split()[-1].replace('*', '').replace(',', ''))
            if a.count('P/E') > 0 and a.count('F P/E') == 0:
                pe = float(a.split()[-1])

        text += ('\nPrice Target: %s' % str(eps * pe))
        return text.replace("\n", "<br>")
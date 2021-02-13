import lxml.html
import aiohttp


async def stockgrab(url):
    """Grabs some information abouts stocks from yahoo finance."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36"
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as page:
            soup = lxml.html.fromstring(await page.text())
    stockdata = []
    for table in soup.xpath('.//table[@class="W(100%)"]'):
        table_body = table.find("tbody")
        rows = table_body.findall("tr")
        for row in rows:
            cols = row.findall("td")
            cols = [ele.text_content().strip() for ele in cols]
            stockdata.append([ele for ele in cols if ele])
    return stockdata


async def stockupdate(data, url):
    for stock in await stockgrab(url):
        if float(stock[2]) >= 1 or stock[0][:3] in data["stocks"]:
            try:
                data["stocks"][stock[0][:3]]["price"] = stock[2]
            except KeyError:
                data["stocks"][stock[0][:3]] = {}

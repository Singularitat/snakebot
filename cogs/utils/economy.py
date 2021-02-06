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

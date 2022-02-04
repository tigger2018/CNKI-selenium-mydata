#encoding:utf8
'''
    知网论文数据爬取
'''
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import requests
import csv


# 定义论文类
class Paper:
    def __init__(self, title, authors):
        self.title = title
        self.authors = authors

# 定义作者类
class Author:
    def __init__(self,name, college, major):
        self.name = name
        self.college = college
        self.major = major


# 进入知网首页并搜索关键词
def driver_open(driver, key_word):
    url = "https://www.cnki.net/"
    driver.get(url)
    time.sleep(2)
    driver.find_element_by_css_selector('#txt_SearchText').send_keys(key_word)
    time.sleep(2)
    # 点击搜索按钮
    driver.find_element_by_css_selector('body > div.wrapper.section1 > div.searchmain > div > div.input-box > input.search-btn').click()
    time.sleep(5)
    content = driver.page_source.encode('utf-8')
    # driver.close()
    soup = BeautifulSoup(content, 'lxml')
    return soup

def spider(driver, soup, papers):
    tbody = soup.find_all('tbody')
    tbody = BeautifulSoup(str(tbody[0]), 'lxml')
    tr = tbody.find_all('tr')
    for item in tr:
        tr_bf = BeautifulSoup(str(item), 'lxml')

        td_name = tr_bf.find_all('td', class_ = 'name')
        td_name_bf = BeautifulSoup(str(td_name[0]), 'lxml')
        a_name = td_name_bf.find_all('a')
        # get_text()是获取标签中的所有文本，包含其子标签中的文本
        title = a_name[0].get_text().strip()
        print("title : " + title)


        td_author = tr_bf.find_all('td', class_ = 'author')
        td_author_bf = BeautifulSoup(str(td_author), 'lxml')
        a_author = td_author_bf.find_all('a')
        authors = []
        # 拿到每一个a标签里的作者名
        for author in a_author:
            skey, code = get_skey_code(author)  # 获取作者详情页url的skey和code
            name = author.get_text().strip()    # 获取学者的名字
            print('name : ' + name)
            college, major = get_author_info(skey, code)  # 在作者详情页获取大学和专业, major是一个数组
            au = Author(name, college, major)   # 创建一个学者对象
            authors.append(au)

        print('\n')
        paper = Paper(title, authors)
        papers.append(paper)
        time.sleep(1)   # 每调一次spider休息1s


# pn表示当前要爬的页数
def change_page(driver, pn):
    driver.find_element_by_css_selector('#page' + str(pn)).click()
    time.sleep(5)
    content = driver.page_source.encode('utf-8')
    soup = BeautifulSoup(content, 'lxml')
    return soup

# 获取作者详情页url的skey和code, 传入参数是一个a标签
def get_skey_code(a):
    skey = a.get_text().strip()
    href = str(a.get('href'))    # 拿到a标签href的值
    code = href[href.find('acode') + 6:]    # 拿到code的值
    return skey, code

# 获取作者的详细信息
def get_author_info(skey, code):
    url = 'https://kns.cnki.net/kcms/detail/knetsearch.aspx?dbcode=CAPJ&sfield=au&skey=' + skey + '&code=' + code + '&v=3lODiQyLcHhoPt6DbD%25mmd2FCU9dfuB5GXx8ZJ7nSrKZfD6N9B5gKP9Ftj%25mmd2B1IWA1HQuWP'
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.133 Safari/569.36',
        'Connection': 'close'
    }
    requests.packages.urllib3.disable_warnings()
    rsp = requests.get(url, headers = header, verify = False)
    rsp_bf = BeautifulSoup(rsp.text, 'lxml')
    div = rsp_bf.find_all('div', class_ = 'wrapper')
    # 有的学者查不到详细信息
    if div:
        div_bf = BeautifulSoup(str(div[0]), 'lxml')
        h3 = div_bf.find_all('h3')
        college = h3[0].get_text().strip()
        major = h3[1].get_text().strip()
        # major = major.split(';')[0: -1]
        print('college:' + college)
        print('major: ' + major)
        return college, major
    print("无详细信息")
    return None, None

if __name__ == '__main__':
    driver = webdriver.Chrome(r"C:\Users\小老虎\Desktop\chromedriver.exe")
    soup = driver_open(driver, '知识图谱')  # 搜索知识图谱
    papers = []     # 用于保存爬取到的论文
    # 将爬取到的论文数据放入papers中
    spider(driver, soup, papers)
    for pn in range(2, 31):
        content = change_page(driver, pn)
        spider(driver, content, papers)
    driver.close()


    # 写入文件
    f_papers_authors = open('./paper_author.csv', 'w', encoding = 'utf-8', newline = '')
    writer_p_a = csv.writer(f_papers_authors)  # 基于文件对象构建 csv写入对象
    writer_p_a.writerow(["name", "college", "major", "paper"])    # csv文件的表头
    
    # 读取每一篇论文
    for paper in papers:
        # 写入paper_author.csv文件
        for author in paper.authors:
            if author.name:
                # print(author + "  ")
                writer_p_a.writerow([author.name, author.college, author.major, paper.title])

    # 关闭文件
    f_papers_authors.close()

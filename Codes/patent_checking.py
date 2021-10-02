####
import requests
from bs4 import BeautifulSoup
import json

class Patents():

    def __init__(self, urls_path):

        self.urls_path = urls_path
        self.urls = []
        self.sources_info = {}
        self.relations = {}
        with open('../Files/source.json', 'r') as infile:
            self.sources_info = json.loads(infile.read())
        self.new_patents = {}


        file1 = open("../Files/source.txt", "w")
        file1.write('{0:<15} {1:<40} {2:<20} {3:<25}\n'.format('ID', 'Name',  'Data', 'Title'))
        file1.write('-'*150)
        file1.write('\n')
        file1.close()

        file1 = open("../Files/relation.txt", "w")
        file1.write('{0:<15} {1:<15}\n'.format('Source', 'Target'))
        file1.write('-' * 25)
        file1.write('\n')
        file1.close()


    def store_urls(self):

        with open(self.urls_path) as fp:
            self.urls = fp.readlines()

    def Read_patents(self):

        count = 0
        for url in self.urls[1:]:

            count += 1
            # time.sleep(0.1)
            res_contents, patent_ID, req = self.request_to_patent_new(url)
            print('url :', count)
            print(req)

            self.relations[patent_ID] = []

            ref_count = 0
            for r in res_contents[16:]:

                ref_count += 1
                if len(r) == 2:

                    ref_url = r[1].attrs['href']
                    if ref_url[0:4] != 'http':
                        ## new ref mode
                        ref_url = 'https://patft.uspto.gov' + ref_url
                        ref_patent_ID = r[1].text
                        ref_req = 'with_no_req'
                        if ref_patent_ID not in self.sources_info.keys():
                            _, ref_patent_ID, ref_req = self.request_to_patent_new(ref_url)

                        elif ref_patent_ID not in self.new_patents.keys():

                            self.new_patents[ref_patent_ID] = 1
                            self.save_to_SourceFile([ref_patent_ID] + self.sources_info[ref_patent_ID])

                        self.relations[patent_ID].append(ref_patent_ID)

                        print('url %i : %i --- %s' % (count, int(ref_count/3), ref_req))

                    else:
                        ## old ref mode
                        ref_patent_ID = ''.join(r[1].text.split('/'))
                        ref_req = 'with_no_req'
                        if ref_patent_ID not in self.sources_info.keys():
                            _, ref_patent_ID, ref_req = self.request_to_patent_old(ref_url)

                        elif ref_patent_ID not in self.new_patents.keys():

                            self.new_patents[ref_patent_ID] = 1
                            self.save_to_SourceFile([ref_patent_ID] + self.sources_info[ref_patent_ID])

                        self.relations[patent_ID].append(ref_patent_ID)

                        print('url %i : %i --- %s' % (count, int(ref_count/3), ref_req))

            self.relations[patent_ID] = set(self.relations[patent_ID])

            for ref_pat_ID in self.relations[patent_ID]:
                self.save_to_RelationFile([patent_ID, ref_pat_ID])


    def request_to_patent_new(self, url):

        req = requests.get(url, headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8",
                                         "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15"})
        soup = BeautifulSoup(req.text, 'html.parser')

        ## Extract Name:
        res_left = soup.find_all('td', attrs={'align': 'left'})
        res_Name = res_left[2].text
        res_Name = ', '.join([s.strip() for s in res_Name.split(',')]).strip()

        ## Extract ID & Date:
        res_right = soup.find_all('td', attrs={'align': 'right'})
        res_ID = ''.join(res_right[1].text.split(',')).strip()
        res_Date = res_right[2].text.strip()

        ## Extract Title:
        res_center = soup.find_all('font', attrs={'size': '+1'})
        res_Title = ''.join(res_center[0].text.split('\n    ')).strip()

        res_contents = []

        if res_ID not in self.sources_info.keys():

            self.sources_info[res_ID] = [res_Name, res_Date, res_Title]

            with open('../Files/source.json', 'wb') as outfile:
                outfile.write(json.dumps(self.sources_info).encode("utf-8"))

        if res_ID not in self.new_patents.keys():

            self.new_patents[res_ID] = 1
            self.save_to_SourceFile([res_ID] + self.sources_info[res_ID])


        for r in res_left:
            res_contents.append(r.contents)

        return res_contents, res_ID, req

    def request_to_patent_old(self, url):

        req = requests.get(url, headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8",
                                         "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15"})
        soup = BeautifulSoup(req.text, 'html.parser')
        res = soup.find_all('td', attrs={'valign': 'top'})

        ## Extract new url
        new_url = 'https://appft.uspto.gov' + res[1].contents[0].attrs['href']
        new_req = requests.get(new_url, headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8",
                                         "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15"})
        soup = BeautifulSoup(new_req.text, 'html.parser')

        ## Extract Name:
        res_left = soup.find_all('td', attrs={'align': 'LEFT', 'width': '50%'})
        res_Name = res_left[2].text
        res_Name = ', '.join([s.strip() for s in res_Name.split(';')]).strip()

        ## Extract ID & Date
        res_right = soup.find_all('td', attrs={'align': 'RIGHT', 'width': '50%'})
        res_ID = res_right[0].text.strip()
        res_Date = res_right[2].text.strip()

        ## Extract Title
        res_center = soup.find_all('font', attrs={'size': '+1'})
        res_Title = ''.join(res_center[0].text.split('\n    ')).strip()

        ## Save contents of patents:
        res_contents = []
        if res_ID not in self.sources_info.keys():

            self.sources_info[res_ID] = [res_Name, res_Date, res_Title]

            with open('../Files/source.json', 'wb') as outfile:
                outfile.write(json.dumps(self.sources_info).encode("utf-8"))

        if res_ID not in self.new_patents.keys():

            self.new_patents[res_ID] = 1
            self.save_to_SourceFile([res_ID] + self.sources_info[res_ID])

        for r in res_left:
            res_contents.append(r.contents)

        return res_contents, res_ID, new_req


    def save_to_SourceFile(self, info):

        file1 = open("../Files/source.txt", "a")  # append mode
        file1.write("{0:<15} {1:<40} {2:<20} {3:<25}\n\n".format(info[0], info[1], info[2], info[3]))
        file1.close()

    def save_to_RelationFile(self, info):

        file1 = open("../Files/relation.txt", "a")
        file1.write('{0:<15} {1:<15}\n'.format(info[0], info[1]))
        file1.close()
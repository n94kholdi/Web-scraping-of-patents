from patent_checking import Patents

urls_path = "../Files/urls.txt"
Mypatent = Patents(urls_path)
Mypatent.store_urls()
Mypatent.Read_patents()

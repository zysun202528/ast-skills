from data_loader import TencentDataLoader

loader = TencentDataLoader()
df = loader.get_index_history("sh000001", days=1)
print(df)

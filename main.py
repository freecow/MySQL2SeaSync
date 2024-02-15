import json
import pymysql
from seatable_api import Base
from dotenv import load_dotenv
import os

# 加载 .env 文件中的环境变量
load_dotenv()

# 从 .env 文件中读取敏感配置
mysql_config = {
    'host': os.getenv('MYSQL_HOST'),
    'port': int(os.getenv('MYSQL_PORT')),  # 确保转换为正确的类型
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'db': os.getenv('MYSQL_DATABASE')
}

seatable_config = {
    'server_url': os.getenv('SEATABLE_SERVER_URL'),
    'api_token': os.getenv('SEATABLE_API_TOKEN')
}

# Load configurations
with open('memo-contract.json', 'r') as f:
    config = json.load(f)

seatable_mappings = config['seatable']
data_mappings = config['data_mappings']
chunk_size = config['chunk_size']

# 函数：清空Seatable表格
def clear_table(base):
    sql = f"DELETE FROM `{seatable_mappings['table_name']}`"
    base.query(sql)

# 函数：执行SQL查询
def execute_sql_query(connection, sql_query):
    with connection.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(sql_query)
        return cursor.fetchall()

# 函数：基于映射处理数据
def process_data_based_on_mapping(data, field_mappings):
    processed_data = []
    for item in data:
        row_data = {seatable_field: item[mysql_field] for mysql_field, seatable_field in field_mappings.items()}
        processed_data.append(row_data)
    return processed_data

# 函数：将数据分批插入到Seatable
def insert_data_into_seatable(base, data, table_name, chunk_size):
    for chunk in chunked_data(data, chunk_size):
        base.batch_append_rows(table_name, chunk)

# 函数：分批处理数据
def chunked_data(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

# 函数：应用合并规则
def apply_merge_rules(main_data, additional_data, merge_rules):
    on_field = merge_rules["on"]
    target_field = merge_rules["target_field"]

    # 创建一个基于on_field的查找字典，用于快速找到main_data中的对应行
    main_data_lookup = {item[on_field]: item for item in main_data}

    # 遍历附加数据，根据合并规则更新主数据集
    for item in additional_data:
        key = item[on_field]
        if key in main_data_lookup:
            # 如果找到匹配的行，更新target_field
            main_data_lookup[key][target_field] = item[target_field]


# 函数：主同步
def sync_mysql():
    """Sync database into the table
    """
    # base initiated and authed
    base = Base(seatable_config['api_token'], seatable_config['server_url'])
    base.auth()

    # Clear table
    clear_table(base)

    # mysql data
    connection = pymysql.connect(
            host=mysql_config['host'],
            port=mysql_config['port'],
            user=mysql_config['user'],
            password=mysql_config['password'],
            db=mysql_config['db'],
            cursorclass=pymysql.cursors.DictCursor
    )

    main_data = []
    additional_data = {}

    try:
        for mapping in data_mappings:
            data = execute_sql_query(connection, " ".join(mapping["sql_query"]))
            processed_data = process_data_based_on_mapping(data, mapping["field_mappings"])

            if "merge_rules" in mapping:
                # 如果有合并规则，暂存处理过的数据用于后续合并
                additional_data[mapping["description"]] = processed_data
            else:
                # 存储主数据集
                main_data = processed_data

        # 如果存在需要合并的数据
        if additional_data:
            for description, data in additional_data.items():
                merge_rules = next(filter(lambda m: m.get("description") == description, data_mappings), {}).get("merge_rules", {})
                apply_merge_rules(main_data, data, merge_rules)

        # 插入到Seatable
        insert_data_into_seatable(base, main_data, seatable_mappings['table_name'], chunk_size)

    finally:
        connection.close()


if __name__ == '__main__':
    sync_mysql()

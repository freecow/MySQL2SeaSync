# MySQL2SeaSync
MySQL2SeaSync is a powerful and efficient tool designed to automate the process of extracting data from MySQL databases and seamlessly syncing it into SeaTable tables, using unique identifiers for accurate and reliable data integration. This utility bridges the gap between relational databases and collaborative online tables, facilitating data migration, reporting, and analysis workflows.

`MySQL2SeaSync`是一个专门设计用于从MySQL中提取数据，自动填写到Seatable表中的工具。特别适合日常工作中，需要从已有的管理系统中抽取数据导入到Seatable中进行分析，结合Seatable强大的表格处理和分析功能，对数据进一步分析的场景。

## 特性

- **自动数据同步**：从MySQL中自动提取数据到Seatable云端。
- **配置驱动**：通过简单的JSON配置，定制化需同步的数据字段。
- **安全性**：敏感信息如数据库凭证、API密钥等存放在`.env`文件，避免硬编码。

## 安装

本工具依赖于Python环境。确保你的系统已安装Python 3.6+。使用以下步骤安装所需的依赖包：

1. 克隆本仓库到本地：

```bash
git clone https://github.com/freecow/MySQL2SeaSync.git
cd MySQL2SeaSync
```

2. 安装所需的Python依赖包：

```bash
pip install -r requirements.txt
```

## 配置

### `.env` 文件

将你的敏感信息如Seatable的`server_url`和`api_token`，以及MySQL的连接参数放在.env文件中放在`.env`文件中。示例内容如下：

```plaintext
SEATABLE_SERVER_URL=https://cloud.seatable.cn
SEATABLE_API_TOKEN=your_api_token_here
MYSQL_HOST=your_mysql_host
MYSQL_PORT=your_mysql_port
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=your_mysql_db
```

确保`.env`文件不被提交到版本控制系统中（比如通过`.gitignore`）。

SEATABLE_API_TOKEN请参考Seatable官方开发文档。

### `config.json` 文件

在`config.json`中定义你的业务信息，如数据映射和同步规则。示例结构如下：

```json
{
  "seatable": {
    "table_name": "你的Seatable表名",
    "name_column": "你的Seatable表关联字段"
  },
  "chunk_size": 900,
  "data_mappings": [
    {
      "description": "主表数据",
      "sql_query": ["..."],
      "field_mappings": {...}
    },
    {
      "description": "X表数据",
      "sql_query": ["..."],
      "field_mappings": {...},
      "merge_rules": {
        "merge_into": "主表数据",
        "on": "...",
        "target_field": "..."
      }
    }
  ]
}
```

### 示例

- 通过`合同编号`关联字段，从MySQL中读取主表数据定义的SQL查询字段，包括合同编号、项目名称、年份及合同金额，年份选择从2017~2024年，写到与Seatable定义好的映射字段。

- 从MySQL中读取子表pro_tag，读取内容包括合同编号、标签，该表合同编号与标签内容为一对多的关系，标签读取后采用逗号分割并组合，写到与Seatable定义好的映射字段。

- 依据合并规则，将组合后的标签合并到主表中合同编号对应的记录。

- 透过JSON定义的业务逻辑，基本上不需要修改主程序main.py。

- chunk_size设置为900，主要是因为Seatable对单次数据处理量的限制为1000.


```json
{
  "seatable": {
    "table_name": "确认收入",
    "name_column": "合同编号"
  },
  "chunk_size": 900,
  "data_mappings": [
    {
      "description": "主表数据",
      "sql_query": [
        "SELECT",
        "  ptc.contract_code,",
        "  ptc.total_project_name,",
        "  ptc.contract_year,",
        "  IFNULL(ptc.contract_amount, '') AS contract_amount,",
        "FROM project_total_contract ptc",
        "WHERE ptc.contract_year IN (2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024);"
      ],
      "field_mappings": {
        "contract_code": "合同编号",
        "total_project_name": "项目名称",
        "contract_amount": "合同金额",
        "contract_year": "年份"
      }
    },
    {
      "description": "pro_tag表数据",
      "sql_query": [
        "SELECT",
        "pro_code,",
        "GROUP_CONCAT(tag_content SEPARATOR ', ') AS tags",
        "FROM pro_tag",
        "GROUP BY pro_code;"
      ],
      "field_mappings": {
        "pro_code": "合同编号",
        "tags": "标签"
      },
      "merge_rules": {
        "merge_into": "主表数据",
        "on": "合同编号",
        "target_field": "标签"
      }
    }
  ]
}
```

## 使用

Seatable中配置好相应的表格，如上例中配置表名为`确认收入`，字段包括`合同编号`、`项目名称`、`合同金额`、`年份`、`标签`。

MySQL中配置好相应的连接，并确保相应的表中有数据。

本地配置好`.env`和`config.json`文件后，运行以下命令启动数据同步：

```bash
python main.py
```

确保`main.py`是你的主程序入口文件。

## 安全性提示

- 不要在任何公共或不安全的地方暴露你的`.env`文件或`config.json`中的敏感信息。
- 定期更新你的Seatable API Token以保持安全。

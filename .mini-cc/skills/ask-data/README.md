# ask-data skill

电子病历问数 skill，通过 Dify 接口完成 SQL 生成和执行。

## 环境变量

```bash
export EHR_DIFY_API_KEY="app-..."
export EHR_DIFY_URL="http://10.58.198.219:8880/v1/chat-messages"
```

`EHR_DIFY_URL` 可省略，脚本内置当前测试地址。

## 业务参考文件

已内置电子病历问数口径，供 Agent 规划 SQL 前读取：

- `references/ehr-result-qa.md`：主口径，表选择、期别、排序、无效上传解释。
- `references/ehr-result-qa-schema.md`：表结构和字段。
- `references/ehr-result-qa-metrics.md`：指标计算规则。
- `references/ehr-result-qa-sql-templates.md`：常见 SQL 模板。

`SKILL.md` 里额外补了“最近两期变化 / 下降最多 / 无效上传追查”的固定拆解策略。

## 手动测试

生成 SQL：

```bash
python .mini-cc/skills/ask-data/scripts/ehr_api.py generate \
  --query "查询各医疗机构电子病历上传总量前10名"
```

执行 SQL：

```bash
python .mini-cc/skills/ask-data/scripts/ehr_api.py execute \
  --sql "SELECT 1"
```

## mini-cc 使用

```bash
mini-cc "/ask-data 查询各医疗机构电子病历上传总量前10名"
```

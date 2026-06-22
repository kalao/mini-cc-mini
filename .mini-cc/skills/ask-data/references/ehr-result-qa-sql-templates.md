---
name: ehr-result-qa-sql-templates
description: 电子病历结果表问数 SQL 模板模块，提供接口调用、开通状态、上传汇总、无效上传汇总和无效上传明细的 PostgreSQL 只读查询模板。
---

# SQL 模板

所有模板只能作为单条只读 `SELECT` 或 `WITH ... SELECT` 使用。执行前按用户问题替换日期、机构、区划、机构等级等条件。

数量字段安全转换表达式：

```sql
CASE
  WHEN NULLIF(TRIM(<数量字段>), '') ~ '^[0-9]+(\.[0-9]+)?$'
  THEN NULLIF(TRIM(<数量字段>), '')::numeric
  ELSE 0
END
```

## 接口调用情况全量明细

```sql
SELECT
  "序号",
  "区划",
  "机构等级",
  "机构编码",
  "机构名称",
  "trns_4301成功数",
  "trns_4301失败数",
  "trns_4302成功数",
  "trns_4302失败数",
  "trns_4401成功数",
  "trns_4401失败数",
  "trns_4402a成功数",
  "trns_4402a失败数",
  "trns_4501a成功数",
  "trns_4501a失败数",
  "trns_4502a成功数",
  "trns_4502a失败数",
  "trns_4503成功数",
  "trns_4503失败数",
  "trns_4504成功数",
  "trns_4504失败数",
  "trns_4505成功数",
  "trns_4505失败数",
  "trns_4506成功数",
  "trns_4506失败数",
  "trns_4601成功数",
  "trns_4601失败数",
  "trns_4602成功数",
  "trns_4602失败数",
  "trns_4701成功数",
  "trns_4701失败数"
FROM public.dx_lxj_call_dzbl
ORDER BY "序号"
```

## 接口调用成功失败汇总

```sql
SELECT
  "区划",
  SUM("trns_4301成功数" + "trns_4302成功数" + "trns_4401成功数" + "trns_4402a成功数" + "trns_4501a成功数" + "trns_4502a成功数" + "trns_4503成功数" + "trns_4504成功数" + "trns_4505成功数" + "trns_4506成功数" + "trns_4601成功数" + "trns_4602成功数" + "trns_4701成功数") AS 成功次数,
  SUM("trns_4301失败数" + "trns_4302失败数" + "trns_4401失败数" + "trns_4402a失败数" + "trns_4501a失败数" + "trns_4502a失败数" + "trns_4503失败数" + "trns_4504失败数" + "trns_4505失败数" + "trns_4506失败数" + "trns_4601失败数" + "trns_4602失败数" + "trns_4701失败数") AS 失败次数,
  SUM("trns_4301成功数" + "trns_4302成功数" + "trns_4401成功数" + "trns_4402a成功数" + "trns_4501a成功数" + "trns_4502a成功数" + "trns_4503成功数" + "trns_4504成功数" + "trns_4505成功数" + "trns_4506成功数" + "trns_4601成功数" + "trns_4602成功数" + "trns_4701成功数" + "trns_4301失败数" + "trns_4302失败数" + "trns_4401失败数" + "trns_4402a失败数" + "trns_4501a失败数" + "trns_4502a失败数" + "trns_4503失败数" + "trns_4504失败数" + "trns_4505失败数" + "trns_4506失败数" + "trns_4601失败数" + "trns_4602失败数" + "trns_4701失败数") AS 总调用次数
FROM public.dx_lxj_call_dzbl
GROUP BY "区划"
ORDER BY 总调用次数 DESC
```

## 接口开通状态每日明细

```sql
SELECT
  "序号",
  "区划",
  "机构等级",
  "机构编码",
  "机构名称",
  "trns_4301",
  "trns_4302",
  "trns_4401",
  "trns_4402a",
  "trns_4501a",
  "trns_4502a",
  "trns_4503",
  "trns_4504",
  "trns_4505",
  "trns_4506",
  "trns_4601",
  "trns_4602",
  "trns_4701",
  "已完成接口数量",
  "未完成接口数量",
  "较前一日新增完成接口数量",
  "统计日期" AS 数据期别
FROM public.dx_lxj_call_dzbl_comp
WHERE "统计日期" = '<DATE_PERIOD>'
ORDER BY "序号"
```

## 接口开通状态汇总

```sql
SELECT
  "区划",
  COUNT(*) AS 机构数,
  SUM(CASE WHEN "已完成接口数量" = 13 THEN 1 ELSE 0 END) AS 全部完成机构数,
  SUM(CASE WHEN "已完成接口数量" < 13 THEN 1 ELSE 0 END) AS 未全部完成机构数,
  SUM("已完成接口数量") AS 已完成接口总数,
  SUM("未完成接口数量") AS 未完成接口总数,
  ROUND(SUM("已完成接口数量")::numeric / NULLIF(COUNT(*) * 13, 0) * 100, 2) AS 接口平均完成率
FROM public.dx_lxj_call_dzbl_comp
WHERE "统计日期" = '<DATE_PERIOD>'
GROUP BY "区划"
ORDER BY "区划"
```

## 上传情况机构汇总

用于“各机构上传总量分别是多少、上传明细、上传清单”等明细类问题时，默认按 `"序号"` 升序。

```sql
SELECT
  "序号",
  "区划",
  "机构等级",
  "机构编码",
  "机构名称",
  CASE
    WHEN NULLIF(TRIM("上传总数量"), '') ~ '^[0-9]+(\.[0-9]+)?$'
    THEN NULLIF(TRIM("上传总数量"), '')::numeric
    ELSE 0
  END AS 上传总数量,
  "数据期别"
FROM public.dx_lxj_dzbl_scqk
WHERE "数据期别" = '<DATE_PERIOD>'
ORDER BY "序号"
```

## 上传情况机构排名

用于“上传总量最多、上传量排名、TopN”等排名类问题时，按上传总数量降序。

```sql
SELECT
  "序号",
  "区划",
  "机构等级",
  "机构编码",
  "机构名称",
  CASE
    WHEN NULLIF(TRIM("上传总数量"), '') ~ '^[0-9]+(\.[0-9]+)?$'
    THEN NULLIF(TRIM("上传总数量"), '')::numeric
    ELSE 0
  END AS 上传总数量,
  "数据期别"
FROM public.dx_lxj_dzbl_scqk
WHERE "数据期别" = '<DATE_PERIOD>'
ORDER BY 上传总数量 DESC
```

## 上传情况按区划汇总

```sql
SELECT
  "区划",
  COUNT(*) AS 机构数,
  SUM(
    CASE
      WHEN NULLIF(TRIM("上传总数量"), '') ~ '^[0-9]+(\.[0-9]+)?$'
      THEN NULLIF(TRIM("上传总数量"), '')::numeric
      ELSE 0
    END
  ) AS 上传总数量
FROM public.dx_lxj_dzbl_scqk
WHERE "数据期别" = '<DATE_PERIOD>'
GROUP BY "区划"
ORDER BY 上传总数量 DESC
```

## 无效上传机构汇总

用于“哪些机构存在无效上传、列举机构清单、无效上传分别是多少”等清单类问题时，默认按 `"序号"` 升序。

```sql
SELECT
  "序号",
  "区划",
  "机构等级",
  "机构编码",
  "机构名称",
  CASE
    WHEN NULLIF(TRIM("上传总数量"), '') ~ '^[0-9]+(\.[0-9]+)?$'
    THEN NULLIF(TRIM("上传总数量"), '')::numeric
    ELSE 0
  END AS 无效上传总数量,
  "数据期别"
FROM public.dx_lxj_dzbl_scqk_not
WHERE "数据期别" = '<DATE_PERIOD>'
ORDER BY "序号"
```

## 月度无效上传机构清单去重

用于“6 月份哪些机构存在无效上传/未关联就诊 ID，列举机构编码和机构名称”等按月机构清单问题。按机构去重，避免同一机构在多天重复出现。

```sql
SELECT
  "机构编码",
  MAX("机构名称") AS "机构名称"
FROM public.dx_lxj_dzbl_scqk_not
WHERE "数据期别" >= '<MONTH_START>'
  AND "数据期别" < '<NEXT_MONTH_START>'
  AND CASE
        WHEN NULLIF(TRIM("上传总数量"), '') ~ '^[0-9]+(\.[0-9]+)?$'
        THEN NULLIF(TRIM("上传总数量"), '')::numeric
        ELSE 0
      END > 0
GROUP BY "机构编码"
ORDER BY MIN("序号")
```

## 月度无效上传机构汇总

用于按月统计机构无效上传累计数量。按机构汇总，排序默认按 `"序号"`；如果用户问排名，再按累计数量降序。

```sql
SELECT
  "机构编码",
  MAX("机构名称") AS "机构名称",
  SUM(
    CASE
      WHEN NULLIF(TRIM("上传总数量"), '') ~ '^[0-9]+(\.[0-9]+)?$'
      THEN NULLIF(TRIM("上传总数量"), '')::numeric
      ELSE 0
    END
  ) AS 无效上传总数量
FROM public.dx_lxj_dzbl_scqk_not
WHERE "数据期别" >= '<MONTH_START>'
  AND "数据期别" < '<NEXT_MONTH_START>'
GROUP BY "机构编码"
HAVING SUM(
  CASE
    WHEN NULLIF(TRIM("上传总数量"), '') ~ '^[0-9]+(\.[0-9]+)?$'
    THEN NULLIF(TRIM("上传总数量"), '')::numeric
    ELSE 0
  END
) > 0
ORDER BY MIN("序号")
```

## 需要通报机构清单

用于“需要通报的机构有哪些”等清单类问题时，默认按 `"序号"` 升序；如果用户问“无效上传最多/排名”，再按无效上传总数量降序。

```sql
SELECT
  "序号",
  "区划",
  "机构等级",
  "机构编码",
  "机构名称",
  CASE
    WHEN NULLIF(TRIM("上传总数量"), '') ~ '^[0-9]+(\.[0-9]+)?$'
    THEN NULLIF(TRIM("上传总数量"), '')::numeric
    ELSE 0
  END AS 无效上传总数量,
  "数据期别"
FROM public.dx_lxj_dzbl_scqk_not
WHERE "数据期别" = '<DATE_PERIOD>'
  AND CASE
        WHEN NULLIF(TRIM("上传总数量"), '') ~ '^[0-9]+(\.[0-9]+)?$'
        THEN NULLIF(TRIM("上传总数量"), '')::numeric
        ELSE 0
      END > 0
ORDER BY "序号"
```

## 无效上传明细

```sql
SELECT
  interface AS 接口,
  l_type AS 类型,
  fixmedins_code AS 机构编码,
  fixmedins_name AS 机构名称,
  mdtrt_id AS 就诊ID,
  psn_no AS 人员编号,
  mdtrt_sn AS 就诊流水号,
  date_period AS 数据期别
FROM public.dx_lxj_dzbl_total_main_not_mx
WHERE date_period = '<DATE_PERIOD>'
ORDER BY fixmedins_code, interface, mdtrt_id
LIMIT 100
```

## 无效上传明细按机构统计

按月份查询时，不要写 `date_period = 'yyyyMM'`，应使用 `date_period >= 'yyyyMM01' AND date_period < '下月yyyyMM01'`。

```sql
SELECT
  fixmedins_code AS 机构编码,
  MAX(fixmedins_name) AS 机构名称,
  COUNT(*) AS 无效上传明细数,
  COUNT(DISTINCT psn_no) AS 涉及人员数,
  COUNT(DISTINCT mdtrt_id) AS 涉及就诊数
FROM public.dx_lxj_dzbl_total_main_not_mx
WHERE date_period = '<DATE_PERIOD>'
GROUP BY fixmedins_code
ORDER BY 无效上传明细数 DESC
```

## 无效上传明细按接口统计

```sql
SELECT
  interface AS 接口,
  COUNT(*) AS 无效上传明细数,
  COUNT(DISTINCT fixmedins_code) AS 涉及机构数,
  COUNT(DISTINCT psn_no) AS 涉及人员数,
  COUNT(DISTINCT mdtrt_id) AS 涉及就诊数
FROM public.dx_lxj_dzbl_total_main_not_mx
WHERE date_period = '<DATE_PERIOD>'
GROUP BY interface
ORDER BY 无效上传明细数 DESC
```

## 上传与无效上传对比

```sql
WITH
sc AS (
  SELECT
    "机构编码",
    MAX("机构名称") AS 机构名称,
    MAX("区划") AS 区划,
    SUM(
      CASE
        WHEN NULLIF(TRIM("上传总数量"), '') ~ '^[0-9]+(\.[0-9]+)?$'
        THEN NULLIF(TRIM("上传总数量"), '')::numeric
        ELSE 0
      END
    ) AS 上传总数量
  FROM public.dx_lxj_dzbl_scqk
  WHERE "数据期别" = '<DATE_PERIOD>'
  GROUP BY "机构编码"
),
not_sc AS (
  SELECT
    "机构编码",
    SUM(
      CASE
        WHEN NULLIF(TRIM("上传总数量"), '') ~ '^[0-9]+(\.[0-9]+)?$'
        THEN NULLIF(TRIM("上传总数量"), '')::numeric
        ELSE 0
      END
    ) AS 无效上传总数量
  FROM public.dx_lxj_dzbl_scqk_not
  WHERE "数据期别" = '<DATE_PERIOD>'
  GROUP BY "机构编码"
)
SELECT
  sc.区划,
  sc."机构编码",
  sc.机构名称,
  sc.上传总数量,
  COALESCE(not_sc.无效上传总数量, 0) AS 无效上传总数量,
  ROUND(COALESCE(not_sc.无效上传总数量, 0) / NULLIF(sc.上传总数量, 0) * 100, 2) AS 无效上传占比
FROM sc
LEFT JOIN not_sc
  ON sc."机构编码" = not_sc."机构编码"
ORDER BY 无效上传总数量 DESC
```

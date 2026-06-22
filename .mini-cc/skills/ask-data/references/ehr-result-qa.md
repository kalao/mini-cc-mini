---
name: ehr-result-qa
description: 电子病历结果表问数口径。默认基于 dx_lxj_call_dzbl、dx_lxj_call_dzbl_comp、dx_lxj_dzbl_scqk、dx_lxj_dzbl_scqk_not、dx_lxj_dzbl_total_main_not_mx 生成 PostgreSQL 单条只读查询。
---

# 电子病历结果表问数口径

本 skill 用于查询已经落地的电子病历结果表，不从日志表重新计算。SQL 必须是 PostgreSQL 可执行的单条只读查询。

默认允许使用以下结果表：

- `public.dx_lxj_call_dzbl`：电子病历接口调用情况全量表。
- `public.dx_lxj_call_dzbl_comp`：医疗机构接口开通状态每日统计表，按数据期别增量。
- `public.dx_lxj_dzbl_scqk`：电子病历上传情况汇总表，按数据期别增量。
- `public.dx_lxj_dzbl_scqk_not`：电子病历无效上传情况汇总表，按数据期别增量。
- `public.dx_lxj_dzbl_total_main_not_mx`：电子病历无效上传明细表，按数据期别增量。

禁止生成会修改数据的 SQL，包括 `INSERT`、`DELETE`、`TRUNCATE`、`UPDATE`、`CREATE TABLE`。

## 业务分流

- 用户问“接口调用、成功数、失败数、调用量、接口成功失败”时，使用 `public.dx_lxj_call_dzbl`。
- 用户问“接口开通状态、是否完成、完成几个、未完成几个、较前一日新增、每日统计”时，使用 `public.dx_lxj_call_dzbl_comp`。
- 用户问“上传情况、上传数量、上传总量、各类电子病历上传量”时，使用 `public.dx_lxj_dzbl_scqk`。
- 用户问“无效上传、匹配不上、编码不一致、需要通报、异常上传汇总”时，使用 `public.dx_lxj_dzbl_scqk_not`。
- 用户问“无效上传明细、哪些就诊 ID 匹配不上、哪些人员编号匹配不上、通报明细”时，使用 `public.dx_lxj_dzbl_total_main_not_mx`。

## 表关系与定位

接口开通状态线：

```text
dx_lxj_call_dzbl
-> dx_lxj_call_dzbl_comp
```

上传质量线：

```text
dx_lxj_dzbl_scqk
dx_lxj_dzbl_scqk_not
dx_lxj_dzbl_total_main_not_mx
```

两条线业务主题相关，但统计口径不同：

- `dx_lxj_call_dzbl` / `dx_lxj_call_dzbl_comp` 看接口是否调用、是否开通完成。
- `dx_lxj_dzbl_scqk` / `dx_lxj_dzbl_scqk_not` / `dx_lxj_dzbl_total_main_not_mx` 看上传数量、无效上传和通报明细。

除非用户明确要求“接口开通状态和上传情况一起对比”，不要把两条线强行混合。

## 数据期别

- `dx_lxj_call_dzbl` 是全量表，表内没有数据期别字段，不能直接回答“某数据期别的调用情况”。
- `dx_lxj_call_dzbl_comp` 使用 `统计日期` 表示数据期别，格式通常为 `yyyyMMdd`。
- `dx_lxj_dzbl_scqk` 使用 `数据期别`。
- `dx_lxj_dzbl_scqk_not` 使用 `数据期别`。
- `dx_lxj_dzbl_total_main_not_mx` 使用 `date_period`。

`dx_lxj_call_dzbl` 和 `dx_lxj_call_dzbl_comp` 的接口字段使用 `trns_` 前缀，且 `4402a`、`4501a`、`4502a` 中的 `a` 为小写。不要生成 `"4301失败数"`、`"4301"`、`"4402A"` 这类不存在的字段。

如果用户问某日、某期、截止某天，默认转成 `yyyyMMdd` 数据期别过滤。

如果用户按月份查询，例如“6月份”“2026 年 6 月”，而目标表的数据期别字段是日粒度 `yyyyMMdd`，必须使用整月范围过滤，不要写成 `= 'yyyyMM'`：

```sql
-- 中文字段数据期别
"数据期别" >= '20260601' AND "数据期别" < '20260701'

-- 英文字段 date_period
date_period >= '20260601' AND date_period < '20260701'
```

如果用户问“最近一期”，先用目标表的期别字段取最大期别，再按该期别过滤。

## 排序规则

- 用户问“最多、最高、排名、TopN、前几名、最大、最少、最低”等排名类问题时，按目标指标值排序。
- 用户问“分别是多少、明细、清单、情况、列表、有哪些”等明细类问题时，默认按业务序号升序排序。
- 如果结果表有 `"序号"` 字段，明细类查询优先使用 `ORDER BY "序号" ASC`。
- 如果用户明确指定排序方式，以用户要求为准。

## 去重与汇总

`dx_lxj_call_dzbl_comp`、`dx_lxj_dzbl_scqk`、`dx_lxj_dzbl_scqk_not`、`dx_lxj_dzbl_total_main_not_mx` 都是按数据期别增量保存的结果表。

如果用户按月、按时间范围查询“有哪些机构、列举机构、机构清单”，必须按机构去重或汇总，避免同一机构因多个数据期别重复出现。

- 只要求列举机构编码、机构名称：按机构编码分组，机构名称使用 `MAX()`。
- 需要数量：按机构编码分组后 `SUM()` 对应数量字段。
- 有 `"序号"` 字段的机构级结果表，排序使用 `ORDER BY MIN("序号") ASC`，除非用户明确要求按数量排名。
- 从 `dx_lxj_dzbl_total_main_not_mx` 查询机构清单时，按 `fixmedins_code` 分组，机构名称使用 `MAX(fixmedins_name)`。

## 无效上传口径

电子病历上传数据中的就诊 ID、人员编号必须与结算记录对应字段保持一致。若就诊 ID 或人员编号无法与结算记录匹配，则判定为无效上传。

- `public.dx_lxj_dzbl_scqk_not`：无效上传机构汇总表，按机构和数据期别汇总。
- `public.dx_lxj_dzbl_total_main_not_mx`：无效上传明细表，按接口、机构、就诊 ID、人员编号、数据期别记录明细。

注意：`dx_lxj_dzbl_scqk_not` 字段名虽然包含“上传数量”，但在该表中代表“无效上传数量”。

## 数量字段处理

`dx_lxj_dzbl_scqk` 和 `dx_lxj_dzbl_scqk_not` 中上传数量字段是 `varchar` 类型。做求和、排序、比较时必须安全转成 numeric：

```sql
CASE
  WHEN NULLIF(TRIM("上传总数量"), '') ~ '^[0-9]+(\.[0-9]+)?$'
  THEN NULLIF(TRIM("上传总数量"), '')::numeric
  ELSE 0
END
```

不要直接对 varchar 数量字段做 `SUM()` 或数值排序。

## 输出要求

- SQL 只能是 `SELECT` 或 `WITH ... SELECT`。
- 最终 SQL 必须是一条可执行 SQL，不要输出多条 SQL。
- SQL 中不得保留 `<DATE_PERIOD>`、`<机构编码>` 等占位符。
- 中文字段必须使用双引号。
- 结果表问数优先查询落地结果表，不要默认回到日志表或机构主数据表重算。

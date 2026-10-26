# 检索与构建审计

日期：2026-10-13，研究任务为联合国体系文化遗产价值界定，用户明确追加中英文语料比较。英文为主要挖掘语言，中文为同文件比较。

## 检索起点与纳入策略

从UNESCO法律事务的conventions/recommendations/declarations目录出发，围绕遗产对象定义、价值判断、社区认可、文化权利、传承与危机保护进行目的性取样。六项核心文化公约为基础，扩展到1999第二议定书、历史景观、文献与数字遗产、博物馆、MONDIACULT文件。不是预注册系统综述；没有声称完成全部联合国文件枚举。

主要实际检索式（搜索引擎和官方目录查阅结合）：

- `QRmine github qualitative research data mining python`
- `site.unesco.org cultural heritage standard setting conventions recommendations declarations`
- `site.unesco.org legal affairs recommendation cultural heritage 1956 1962 1968 1976 2015`
- `site.whc.unesco.org operational guidelines 2025 pdf`
- `site.un.org zh 保护世界文化和自然遗产公约`
- `site.ich.unesco.org Chinese convention 2003 text`
- `site.un.org/zh 保护非物质文化遗产公约`
- `site.un.org/zh 文化多样性宣言`
- `site.un.org/zh 保护和促进文化表现形式多样性公约`
- `site.unesco.org/en/legal-affairs 1954 Convention`，以及1970、2001 Underwater、2005 Diversity
- `site.unesco.org MONDIACULT 2022 declaration culture global public good 2025 report`
- `site.unesco.org MONDIACULT 2025 Outcome`
- `site.un.org cultural heritage resolution 2347 2017 2199 2015`
- `site.ohchr.org A/HRC/17/38 cultural heritage pdf`
- `site.unesco.org global report cultural policies 2025 key findings`
- `site.unesco.org/en/legal-affairs Second Protocol 1999`
- `site.un.org Declaration on the Rights of Indigenous Peoples Article 11 Article 31`
- `site.un.org 2030 11.4 cultural`

最终URL、成功／排除状态及语料范围：`config/sources.json`和`results/source_inventory.csv`。最后两项检索只识别补充方向，未取得并编码其完整原文，不计为覆盖。

## 本轮真实工作步骤

1. 核查本地环境与QRmine官方仓库／PyPI；建立Python3.11环境。
2. 建立官方文件候选清单；下载原始HTML/PDF。部分站点反复发生SSL/代理断连、验证码或访问限制。
3. 对可通过浏览读取的官方页面保存文字快照；这些快照的来源、截取行范围和哈希单独登记。未将搜索摘要当作完整文献。
4. 清洗正文并核查HUL中文PDF，发现多语言和页面外隐藏内容；只保留四段图像核验摘录。截图由工具渲染，中文转录由AI助手对照完成，尚无人类二次核验。
5. 实际调用QRmine获得词项及工具内置词典；运行固定参数的补充NMF。
6. 阅读定义和关键条款，形成解释性代码簿与38条证据锚点；全语料正则匹配仅标为候选。
7. 核查中英文版本范围，特别是2001宣言行动计划差异；回看所有显示为双语范畴存在性不一致的候选，记录五条假阳性。不是全库语义复核。
8. 补充1999第二议定书并重跑挖掘；生成分层统计、双语表、中文报告、完整性验证和离线复跑比对。

## 范畴决策备忘录

- 将“历史／审美／知识／认同／传承／多样性／福祉／场所”放入价值内容；将“真实性／完整性／制度尺度／社区权利”另列；把管理与风险分开。
- 原始机器NMF显现行政措辞主题，故未将其直接命名为遗产价值范畴。
- 代码簿的宽松规则保留了候选召回功能，因而包含多义词误匹配；报告不把其频率等同于确认频率。
- HUL词汇表的文化意义定义源自澳大利亚ICOMOS《布拉宪章》，需保留引用层级。
- 不把非遗的再创造要求与世界遗产真实性条件当成逻辑矛盾；先比较适用对象与制度。
- 不声称存在双人编码、理论饱和或无先验归纳；报告中的核心范畴与关系命题都是待研究者验证的解释。

## 未覆盖范围

完整的专题／年度／国别报告，1954第一议定书，2007土著权利宣言，2030议程及文化指标，2003非遗操作指示和伦理原则，世界遗产气候／可持续发展专题政策，其他语言版本和全部官方新闻等。部分已经发现但未下载成功的报告仍列在排除清单中，不能将其解释为无关证据。

最终边界复查：补齐MONDIACULT2022正文最后第21、22段，将截取终点从L89扩至L92；《信使》1970公约文章限定主体段落L48—74，排除作者简介和Read also。修正后重新完整离线复跑两次。

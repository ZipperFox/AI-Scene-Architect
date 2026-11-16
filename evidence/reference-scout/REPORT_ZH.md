# AI Reference Scout：實作與驗證報告

來源研究：2026-11-15；最終回歸與交付：2026-11-16（Asia/Taipei）。

**結果：PASS，並明確保留研究與美術判斷的限制。** 已完成代理自主研究、來源紀錄、AI 美術主張、Art Direction Brief、Scene Plan 追溯整合及離線方案。沒有修改或合併 main，也沒有重啟已停止的 v0.2 場景修正。

## 核心：AI 自己設計，參考用於啟發

這套功能的目的在於設計及美感。AI 依自己的美感形成構圖、形狀語言、配色、材質與光線，說明考慮過哪些方向、為何選擇現在的設計。參考可以來自真實、幻想、科幻或其他作品，不要求完全寫實，也不要求每個藝術選擇都由外部來源背書。

研究紀錄同時區分現實資訊、作品設定、作者原則、主觀視覺判讀與未知資料。這是防止混淆與抄用的紀錄層，不是用事實清單判定美感的規則。

自主設計不是品質豁免。兩份提案都列出可能不好看的原因與檢視問題；實際畫面仍須檢查構圖、比例、材質、光線與整體完成度。不合格就於既有兩次修正額度內改善，額度用完仍有缺陷則停止並如實回報，不能以「AI 自己的美感」當作驗收理由。本次沒有新場景渲染，因此沒有宣稱新的美術品質已通過。

## Git 與既有架構

- PR #1：open/draft、未合併，HEAD `3a9ee718ffc273f35e915e6e653c4a9753ca3d0d`。
- PR #2：open/draft、未合併，HEAD `b719a36de33a9fb6d7c29da8b28cbe7b96698c81`，依賴 PR #1。
- 本次分支：`feat/ai-reference-scout`，從 PR #2 HEAD 建立；Draft PR 的 base 為 `feat/scene-planning-v02`。
- main 保持 `0760407b9c66112ad2d7df1151788908724e7073`。
- v0.2 使用 AI 寫計畫、Python 驗證／建場。本次沿用此分工：AI 呼叫可用工具搜尋，Python 不內建模型或固定搜尋供應商。
- `prepare_planning.py` 預設先要求 Scout；可接受已編譯研究資料。Schema 新增可選 `research`，既有 v0.2 計畫仍相容。
- `load_plan` 在建場前驗證 manifest、brief 雜湊及決策對應值；建場器把研究 bundle 一同保存。

## 實際成果

| 案例 | AI 自主美術方向 | 搜尋策略與使用方式 |
|---|---|---|
| 礦洞 | **靜默的斷脈**：入口木構的秩序、偏生晶簇、不對稱焦點、克制微光與探索留白 | 從木支撐／運礦用途、礦物資料擴展至幻想場景的功能意象與構圖；借用語彙，捨棄來源的花朵、遺跡圖案及日光題材 |
| 木工作坊 | **午後停工**：暖柔光、工作桌主量體、低長凳、圓形機件與中央呼吸空間 | 從工作檯構造、木材方向與夾具線索出發，原頁失敗後改查實作者；同一可讀性思路轉譯為家具疏密，不沿用礦洞查詢 |

- 礦洞：[reference_manifest.json](../../examples/reference-scout/crystal-mine/reference_manifest.json)、[Art Direction Brief](../../examples/reference-scout/crystal-mine/art_direction_brief.md)、[scene_plan.json](../../examples/reference-scout/crystal-mine/scene_plan.json)。
- 工作坊：[reference_manifest.json](../../examples/reference-scout/woodwork-shop/reference_manifest.json)、[Art Direction Brief](../../examples/reference-scout/woodwork-shop/art_direction_brief.md)、[scene_plan.json](../../examples/reference-scout/woodwork-shop/scene_plan.json)。
- [離線情況示範](../../examples/reference-scout/offline-demo/reference_manifest.json)：明確標示為模擬無搜尋工具，沒有捏造搜尋或來源；不是宣稱本次全部網路工具不可用。

兩組成果包含自主美術主張、未選方案及理由、搜尋問題與實際查詢、來源／觀察／授權、設計決策及其 Scene Plan JSON Pointer。`creative_judgment` 允許無外部引用的原創選擇；`supported_adaptation` 連到可讀來源；未查證條件保留為 `assumption`。

本次產出是**研究及規劃提案**。既有兩組計畫的空間、模型、位置、材質數值、燈光及攝影機資料沒有改動；主要更新美術敘述、配置用途說明與研究追溯。沒有把這些文字提案冒充為已重渲染、已證明更美的場景。

## 實際來源與查核狀態

共 6 個實際文字搜尋查詢、1 個圖片搜尋查詢。美術查詢同時供兩組規劃使用，未假裝重複執行。兩份 manifest 共保留 8 個不同來源，其中 7 個原頁成功開啟、1 個逾時；另實際開啟一張官方作品圖片。來源網址及查核範圍如下。

| 來源 | 用途／已查核資訊 | 狀態／授權 |
|---|---|---|
| [NPS：Quincy Shaft-Rockhouse](https://www.nps.gov/articles/the-no-2-quincy-shaft-rockhouse-9-240-feet-into-the-earth-teaching-with-historic-places.htm) | 木樑地下支撐用途；不據此推導本案承載力 | 原頁文字已讀；重用權利未知 |
| [NPS：Grand Gulch Copper](https://www.nps.gov/para/learn/historyculture/copper-from-discovery-to-boom-to-ruin.htm) | 圖說中的運礦軌道與井架功能 | 圖說文字已讀、未獨立看圖；重用權利未知 |
| [USGS：Quartz Crystal](https://www.usgs.gov/media/images/quartz-crystal) | 館藏石英圖說的透明結構／裂紋；不支持青色自發光 | 原頁文字已讀；該媒體項目明示 Public Domain，範圍不外推 |
| [Riot：The Art of VALORANT Map Environments](https://playvalorant.com/en-gb/news/dev/the-art-of-valorant-map-environments/) | 作者談材質明度、照明與遊戲可讀性的美術原則 | 原頁文字已讀；作品／圖片重用權利未知 |
| [Riot：Lotus](https://playvalorant.com/en-us/news/dev/lotus-unearthing-valorant-s-lost-city/) | 虛構世界中功能與意象呼應的設計；觀察大面、冷暖與少量重點的視覺節奏 | 原頁及一張官方圖已檢視；虛構設計不是物理證據，重用權利未知 |
| [Lost Art Press：Workbench Q&A](https://blog.lostartpress.com/2020/07/30/52-workbench-questions-answers/) | 實作者對工作檯材料、檯面及支撐取捨的說明 | 原頁已讀；作者建議不當作所有桌型的必備規則；重用權利未知 |
| [Lee Valley：Wood Movement](https://www.leevalley.com/en-us/discover/woodworking/2021/january/how-to-cope-with-wood-movement) | 木材方向與接合留位的資訊，轉譯成材料語彙 | 原頁已讀；不複製貼圖或施工圖；重用權利未知 |
| [Smithsonian：Carpenter’s Bench Vise](https://americanhistory.si.edu/collections/object/nmah_656842) | 夾具搜尋線索 | 原頁開啟逾時，只保留 unverified_lead；未用來支持建模決策 |

Lotus 圖片搜尋回傳空結果；後續從官方 HTML 取得圖片 URL 並以本機快取實際開啟。manifest 保存精確 CDN URL、檔案 SHA-256 及主觀觀察。該快取排除於 Git，沒有匯入 Blender 或當作素材再散布。其他未看過的圖片沒有標成 `image_reviewed`。

搜尋結果、網頁及圖片只作資料。程式不執行頁面內容、不自動下載外部 3D 模型／貼圖／作品，也不讓頁面指令改變代理規則。

## 測試與相容性

| 驗證 | 結果 | 證據 |
|---|---|---|
| 全部 Python 單元測試 | **75/75 PASS**，無跳過 | [unit-tests-portability.log](unit-tests-portability.log) |
| 原 v0.1／v0.2 規則與計畫測試 | PASS，包含在 75 項中 | 同上 |
| Provider-neutral 請求、獨立查詢、分類、來源關聯 | PASS | 同上 |
| 幻想設計可作靈感，獨立美感選擇可無引用 | PASS | 同上 |
| 摘要／失敗頁不能冒充已查核事實，未看圖不能冒充視覺觀察 | PASS | 同上 |
| 授權證據、未知權利、資料來源與 JSON Pointer 綁定 | PASS | 同上 |
| 離線不捏造搜尋、可接受本機自有參考 | PASS | 同上 |
| Markdown／HTML 逸出與惡意文字保持資料 | PASS；不是完整 LLM 防護證明 | 同上 |
| Compile／bind CLI 往返、拒絕覆寫、資料或計畫篡改 | PASS | 同上 |
| Blender 原有建模契約 | **4/4 PASS** | [blender-regression.log](blender-regression.log) |
| Blender 研究整合 | **6 項檢查全 PASS** | [blender-portability.json](blender-portability.json) |
| 研究篡改在 Blender 場景變更前拒絕 | PASS | 同上 |
| 研究 bundle 隨計畫保存且搬移後可驗證 | PASS | 同上 |
| 既有證據、場景及兩次修正紀錄保護 | PASS | [preservation-final.json](preservation-final.json) |
| Windows／Git 換行與資料雜湊可攜性 | PASS，輸出明確使用 LF，暫存區實際資料符合計畫中的雜湊 | [git-portability.json](git-portability.json) |

Blender 使用既有 Steam 5.3.0：`D:\SteamLibrary\steamapps\common\Blender\blender.exe`。研究整合測試只在暫存目錄建立地板／木箱技術 fixture 並儲存 `.blend`／GLB，不是重做正式工作坊或礦洞。測試有 Blender 啟動材質路徑與 glTF AREA 燈光警告，未影響檢查；既有匯出限制沒有在此擴大修正。

## 已知限制與下一階段

- Python 不自行理解需求或呼叫網路供應商；自主策略、實際工具調用與美術綜合由 AI 代理完成。範例是這次真實操作的結果，不是固定場景產生器。
- 驗證器可檢查一致性、URL／觀察關聯、雜湊、許可紀錄完整性與引用範圍，不能獨立保證來源真實、授權判讀正確或代理真的看過圖片。這些仍需實際工具證據與誠實紀錄。
- 將資料保留在逸出的 JSON 區塊能減少指令誤升格，不能宣稱完全抵抗所有 prompt injection。代理瀏覽時仍須維持資料／指令邊界。
- 本次只有 Lotus 一張圖片做了視覺觀察；木工作坊及其他真實結構來源主要為文字研究。未宣稱全面視覺比對或新的美術驗收。
- 可在未來需要時增加參考圖縮圖板、代理工具事件的標準化匯入及更細緻的靈感轉譯比較。這些不應變成固定美感評分、強制寫實或限制 AI 原創性的機制。
- 本次未更動 `iteration_guard.py`、`builders.py`、渲染器或既有場景。初次渲染不扣次數、最多兩次自主修正、無整體時間限制、重複／無改善只警告等規則保留。

## 重現

```powershell
python -m unittest discover -s tests -v
python skills/ai-scene-architect/scripts/scene_plan.py examples/reference-scout/crystal-mine/scene_plan.json
python skills/ai-scene-architect/scripts/scene_plan.py examples/reference-scout/woodwork-shop/scene_plan.json
& 'D:/SteamLibrary/steamapps/common/Blender/blender.exe' --background --factory-startup --python-exit-code 1 --python tests/blender_contract_checks.py
& 'D:/SteamLibrary/steamapps/common/Blender/blender.exe' --background --factory-startup --python-exit-code 1 --python tests/blender_reference_scout_checks.py -- '<新的絕對路徑>/result.json'
```

一般測試不重新上網，也不把模擬資料假稱為實際搜尋；即時研究由使用技能的代理另行執行。完整操作與資料契約見 [reference-scout.md](../../skills/ai-scene-architect/references/reference-scout.md)。

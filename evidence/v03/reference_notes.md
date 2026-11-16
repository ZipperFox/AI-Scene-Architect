# 實際參考與設計轉譯

2026-11-16。所有圖片僅作觀察，不取樣作貼圖、不複製模型或作品，不將未授權圖片加入 Git。

## 工作坊：新增並實際開啟的圖片

- 實際圖片搜尋：`traditional woodworker workshop workbench window light museum`。
- [來源頁](https://www.moebelmuseum.de/aktuelles/aktuelle-ausstellung/)、[精確媒體](https://www.moebelmuseum.de/wp-content/uploads/2024/05/Werkstatt-im-Museum-scaled.jpg)。
- 頁面與圖片均已開啟。頁面現有展覽文字可能變動，視覺觀察僅針對精確媒體 URL；hash 與觀察已加入 v0.3 工作坊 reference_manifest。
- 觀察：窗框把光線分段；長向木板、厚檯面、螺桿夾具及牆上工具傳達用途。這是單張類比，不是量測尺寸。
- 落實：真正的開孔窗牆與分格木框、長向桌板、可編輯夾具／刨具、低密度工具架、木地板與午後方向光。
- 捨棄：照片中密集器具與完整寫實磨耗，避免違背《午後停工》的留白、低模與主次。
- 權利：未知；快取 `private-reference-cache/workshop.jpg` 排除於 Git，沒有再散布或匯入場景。

## 礦洞與共同美術：重新開啟已取得的圖片

- [Joanneum 礦坑展覽頁](https://www.museum-joanneum.at/presse/pressetermine/event/cosa-escape)、[媒體](https://www.museum-joanneum.at/fileadmin/user_upload/PRESSE/19_CoSA/Dauerausstellung/Escape_Room/Schaubergwerk_02.jpg)。本次實際開啟保留的本機快取。
- 觀察：木柱、橫樑、上方支撐與岩面有相互承接關係；軌道與料車位於工作路徑。轉譯成支架尺寸／位置與材質區別，沒有複製該展覽布局。
- [Riot Lotus 來源頁](https://playvalorant.com/en-us/news/dev/lotus-unearthing-valorant-s-lost-city/)、[本次重新檢視的媒體](https://cmsassets.rgpub.io/sanity/images/dsfx7636/news_live/05ea5a1b66bf52b9f64eb003903c9962b6c43136-1694x952.jpg)。
- 觀察：寬闊安靜的大面、冷暖分區、少量高處重點、較少裝飾的地面通路。轉譯成場景主次，而非借用其花朵、遺跡圖案或造型。
- 權利：未知；均只作檢視，既有快取與既有紀錄未修改。

## API 與技術查核

- [Blender BooleanModifier API](https://docs.blender.org/api/5.3/bpy.types.BooleanModifier.html)：工作檯初次布林孔洞產生退化幾何，因此捨棄該方案，改以共享頂點的格網構造實作孔洞。失敗建置保留。
- [Blender Image API](https://docs.blender.org/api/current/bpy.types.Image.html?highlight=image+source)：使用生成像素與 `pack()` 保存自己生成的 128×128 PNG albedo；GLB 保留貼圖，沒有外部照片依賴。
- 色彩驗證：程序化 PNG 按 sRGB 編碼，Shader／glTF 再解碼；保存原場景貼圖均值，重開／匯入時比對均值、尺寸、PBR 因子，再實際看圖。此數值檢查不代替美術驗收。

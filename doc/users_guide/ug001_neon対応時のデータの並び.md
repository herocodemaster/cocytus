# ug001 NEON使用時のデータの並び

Neon使用時は、入力層を含むすべてのレイヤーに外枠を確保します。確保する数は水平方向は、左右それぞれ2個、垂直方向は上下それぞれ4個分です。
この領域は0で埋めておき計算に使用する。左端の外枠領域が、右端の外枠領域と共通で使えるため、実際には左端のみ4、右端はパディングのみを行う。

## 左右のパディング
### 横のサイズが4の倍数の時
パデングなしで、左橋に4つ分の外枠を入れ、右端の外枠と共有します。


## 横のサイズが4の倍数でない時
水平方向のデータ数を画素数をxとすると、対応するパディング数は

padding = ((4 - (x%4)) % 4)

で計算します。

VGG16の計算例
```c
#define HPADDING_224 ( (4-(224%4))%4 )
#define HPADDING_112 ( (4-(112%4))%4 )
#define HPADDING_56  ( (4-( 56%4))%4 )
#define HPADDING_28  ( (4-( 28%4))%4 )
#define HPADDING_14  ( (4-( 14%4))%4 )
#define HPADDING_7   ( (4-(  7%4))%4 )
```

## Cソース内での表現
- NEON_HTR 横方法の外枠
- NEON_VTR 縦方向の外枠


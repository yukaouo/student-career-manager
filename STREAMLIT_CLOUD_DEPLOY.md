# Streamlit Community Cloud デプロイ手順

## 目的

外出先のスマホから Career Tree の登録済み内容を確認できるようにする。

## デプロイ設定

- Repository: `yukaouo/student-career-manager`
- Branch: `master`
- Main file path: `student_career_manager.py`

## 必要ファイル

- `student_career_manager.py`
- `requirements.txt`
- `companies_demo.csv`

## 公開デモとして使う場合

`companies.csv` はGit管理しない。
Cloud上では `companies_demo.csv` が読み込まれ、閲覧専用モードで起動する。

## 自分用データをスマホで見る場合

個人データを含むため、GitHubリポジトリとStreamlitアプリを private にする。
そのうえで `companies.csv` を安全に配置する。

## Streamlit Secrets 任意設定

閲覧専用に固定したい場合:

```toml
CAREER_TREE_READ_ONLY = true
```

モード名で指定したい場合:

```toml
CAREER_TREE_MODE = "demo"
```

## 注意

publicリポジトリに本番の就活データやES回答を置かないこと。
ポートフォリオ公開では必ずダミーデータを使う。

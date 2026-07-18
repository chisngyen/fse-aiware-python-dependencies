CGAR Q&A — Hybrid search (vector embedding + từ khóa/synonym)
=============================================================

CÁCH CHẠY (offline hoàn toàn, không cần mạng):
  1. Double-click  start.bat   (Windows, cần đã cài Python 3)
  2. Trình duyệt tự mở http://localhost:8000/index.html
  3. Lần đầu chờ vài giây: góc phải hiện "vector: đang tải… -> sẵn sàng ✓"
     (nạp model e5-small ~112MB chạy ngay trong trình duyệt, offline).
  4. Gõ câu hỏi. Nhấn Ctrl+C ở cửa sổ đen để tắt server.

Nếu không có Python: cài Python 3 (python.org) rồi chạy lại start.bat.
Mac/Linux: mở terminal trong thư mục này, chạy:  python3 serve.py

CƠ CHẾ:
  - Lexical + synonym (LLM sinh sẵn): tức thì, chính xác cho số slide,
    thuật ngữ, số liệu, gõ sai 1 ký tự (fuzzy).
  - Vector e5 (đa ngôn ngữ, 384 chiều): chạy local qua onnxruntime WASM,
    dùng làm tiebreak + cứu paraphrase. Trên tập 89 câu kỹ thuật này
    vector đóng góp biên (cosine bị nén), nên được ghìm nhẹ để không
    gây nhiễu; phần lớn chất lượng đến từ lexical + synonym.
  - Nếu vector nạp lỗi (máy chặn WASM), app tự chạy chế độ chỉ-từ-khóa.

Bản 1-file không cần server: ../qa-search.html (double-click, không vector,
chất lượng tương đương cho hầu hết câu).

THÀNH PHẦN:
  index.html          app
  data.js             89 câu Q&A + synonym index
  lib/                transformers.js + onnxruntime WASM
  models/             model e5-small (config, tokenizer, onnx q8)
  serve.py            server tĩnh (gửi header COOP/COEP cho WASM threads)
  start.bat           launcher Windows

# 🎯 FSE 2026 Competition - Master Guide

**Competition**: Agentic Python Dependency Resolution  
**Deadline**: February 28, 2026 (12 days left)  
**Your Goal**: Improve PLLM baseline tool

---

## 📋 HIỆN TẠI BẠN Ở ĐÂU?

### ✅ Đã xong (Days 1-2):
1. ✅ Setup môi trường (Docker, Ollama, Gemma2)
2. ✅ PLLM baseline đang chạy
3. ✅ Analyzed 2,895 historical tests
4. ✅ Hiểu PLLM: 40% success rate
5. ✅ Design xong tool cải tiến: expected 65-70%

### ⏳ Cần làm tiếp (Days 3-14):
6. ⏳ **Implement tool của bạn** (Days 3-7)
7. ⏳ Test & evaluate (Days 8-11)
8. ⏳ Write paper 4 pages (Days 12-13)
9. ⏳ Submit (Day 14)

---

## 🎯 YÊU CẦU CỦA BAN TỔ CHỨC

**Đúng!** Bạn cần:

1. **Improve PLLM baseline**
   - PLLM hiện tại: 40% success rate
   - Bạn cần: >40% (càng cao càng tốt)

2. **Submit 2 thứ**:
   - **Tool**: Code trong `tools/your-tool/` (Docker)
   - **Paper**: 4 pages mô tả approach + results

3. **Evaluate trên HG2.9K dataset**
   - 2,900+ Python snippets
   - So sánh với PLLM
   - Report metrics

---

## 🔍 VỀ BASELINE

### PLLM là gì?
- Tool hiện tại của ban tổ chức
- 5-stage pipeline: extract → build → analyze error → retry
- Success rate: ~40%
- **Bạn cần làm tốt hơn nó!**

### Bạn đã test PLLM chưa?
✅ **Đã test** - 3 tests hoàn thành:
- Test 1: FAILED (urllib2)
- Test 2: FAILED (scrapy)
- Batch test: Đang chạy (3/5 done)

### Có cần chạy full baseline không?
**KHÔNG CẦN!** Vì:
- Ban tổ chức đã cho sẵn results: `pllm_results/` (2,895 tests)
- Bạn đã analyze data này rồi
- Biết rõ PLLM fail ở đâu (ImportError 30%, SyntaxError 25%)

**Kết luận**: Đủ data rồi, bắt đầu implement tool của bạn!

---

## 🚀 BÂY GIỜ LÀM GÌ?

### Option 1: Implement tool ngay (RECOMMEND)
**Ưu điểm**: Còn 12 ngày, cần bắt đầu code
**File hướng dẫn**: `SYSTEM_DESIGN.md` + `IMPLEMENTATION_CHECKLIST.md`

### Option 2: Chạy thêm tests để hiểu baseline
**Ưu điểm**: Hiểu sâu hơn
**Nhược điểm**: Mất thời gian, đã có đủ data

---

## 💡 TÔI RECOMMEND

**→ BẮT ĐẦU IMPLEMENT NGAY!**

**Lý do**:
- ✅ Đã có đủ data (2,895 historical tests)
- ✅ Đã hiểu PLLM (40% success, top errors)
- ✅ Đã design xong (3 improvements)
- ⏰ Còn 12 ngày (cần bắt đầu code)

---

## 📂 CHỈ CẦN 4 FILES NÀY:

### 1. `README_START_HERE.md` ⭐⭐⭐ (file này)
**Mục đích**: Overview tổng quan
**Khi nào đọc**: Khi confused

### 2. `SYSTEM_DESIGN.md` ⭐⭐⭐
**Mục đích**: Design tool của bạn (architecture + code)
**Khi nào đọc**: Khi implement

### 3. `IMPLEMENTATION_CHECKLIST.md` ⭐⭐
**Mục đích**: Checklist từng bước
**Khi nào đọc**: Hàng ngày để track progress

### 4. `PLLM_ANALYSIS.md` ⭐
**Mục đích**: Analysis data, improvement ideas
**Khi nào đọc**: Khi viết paper

---

## 🎯 BƯỚC TIẾP THEO (NGAY BÂY GIỜ)

### Nếu muốn implement ngay:

```powershell
# 1. Đọc design
code e:\FSE\SYSTEM_DESIGN.md

# 2. Tạo project
cd e:\FSE\fse-aiware-python-dependencies\tools
mkdir smart-resolver
cd smart-resolver

# 3. Bắt đầu code theo SYSTEM_DESIGN.md
```

### Nếu muốn test baseline thêm:

```powershell
# Check batch test progress
cd e:\FSE\fse-aiware-python-dependencies\tools\pllm

# Run more tests (will take 1-2 hours)
docker exec pllm-test python test_executor.py -f '/gists/[SNIPPET_ID]/snippet.py' -m 'gemma2' -b 'http://ollama:11434' -l 2 -r 0
```

---

## 📊 BASELINE SUMMARY (Đã có data)

**Từ 2,895 historical tests**:
- Success: 40%
- Failures:
  - ImportError: 30%
  - SyntaxError: 25%
  - Other: 45%
- Avg time: 7 minutes
- Python 2.7: 60% of tests
- Python 3.x: 40% of tests

**→ ĐỦ DATA RỒI! Không cần test thêm!**

---

## 💡 RECOMMENDATION CỦA TÔI

**Bắt đầu implement tool NGAY!**

**Lý do**:
1. Đã có đủ understanding về baseline
2. Đã có design rõ ràng
3. Còn 12 ngày - cần code ngay
4. Test thêm = waste time

**Timeline**:
- Days 3-7: Code tool (5 days)
- Days 8-11: Evaluate (4 days)
- Days 12-14: Paper (3 days)

---

## 🚀 ACTION NGAY:

### Step 1: Đọc design (15 phút)
```powershell
code e:\FSE\SYSTEM_DESIGN.md
```

### Step 2: Tạo project (5 phút)
```powershell
cd e:\FSE\fse-aiware-python-dependencies\tools
mkdir smart-resolver
cd smart-resolver
mkdir src
mkdir tests
```

### Step 3: Start coding (theo SYSTEM_DESIGN.md)
Implement 3 components:
1. PythonVersionDetector
2. PyPIValidator  
3. ModuleMapper

---

## ❓ CÂU HỎI CỦA BẠN

### "Tôi nên làm gì?"
→ **Implement tool theo SYSTEM_DESIGN.md**

### "Đang làm gì?"
→ **Đã xong research phase, bắt đầu implementation phase**

### "Thiếu gì?"
→ **Thiếu code tool (chưa viết)**

### "Có cần chạy full baseline không?"
→ **KHÔNG! Đã có data từ 2,895 tests rồi**

### "Yêu cầu là improve baseline?"
→ **ĐÚNG! Làm tool tốt hơn PLLM (>40% success)**

---

## 🎯 QUY TRÌNH RÕ RÀNG

```
[Bạn ở đây]
    ↓
Day 3-7: Write code (implement 3 improvements)
    ↓
Day 8-11: Test tool trên HG2.9K dataset
    ↓
Day 12-14: Write paper + Submit
    ↓
[Done!]
```

---

## ✅ QUYẾT ĐỊNH NGAY:

**A.** Bắt đầu implement tool (RECOMMEND) ✅

**B.** Test baseline thêm vài ngày (NOT RECOMMEND) ❌

**Chọn A hay B?** 🤔

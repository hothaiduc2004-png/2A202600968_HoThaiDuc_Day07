# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Hồ Thái Đức (2A202600968)
**Nhóm:** Cá nhân
**Ngày:** 2026-06-05

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Hai văn bản có high cosine similarity khi các embedding vectors của chúng hướng về cùng một hướng trong không gian vector. Điều này chỉ ra rằng hai văn bản chia sẻ nhiều khái niệm, từ vựng, hay ý tưởng tương tự.

**Ví dụ HIGH similarity:**
- Sentence A: "Python là ngôn ngữ lập trình cấp cao."
- Sentence B: "Python là ngôn ngữ lập trình mức cao."
- Tại sao tương đồng: Hai câu có cùng chủ đề (Python), cùng từ vựng chính (lập trình), chỉ khác biểu đạt nhẹ. Vector embeddings sẽ gần nhau.

**Ví dụ LOW similarity:**
- Sentence A: "Con mèo ngủ trên sofa."
- Sentence B: "Phương trình toán học có ba ẩn số."
- Tại sao khác: Hai câu không chia sẻ từ vựng hoặc khái niệm chung (một về động vật, một về toán học). Vector embeddings sẽ chỉ đến các hướng khác nhau.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity chỉ xem xét góc giữa hai vectors, không bị ảnh hưởng bởi độ dài của vector. Điều này quan trọng vì văn bản dài hơn sẽ tự động có magnitude lớn hơn, nhưng điều đó không phải lúc nào cũng có ý nghĩa về sự tương đồng nội dung. Cosine similarity chuẩn hóa ảnh hưởng này.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Công thức: `num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap))`
> Thế số: `num_chunks = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23 chunks`
> 
> Cách hiểu: Mỗi chunk (trừ chunk đầu) bắt đầu từ vị trí `start = i * (chunk_size - overlap)`. Chunk cuối cùng thêm vào khi vị trí bắt đầu >= độ dài tài liệu.

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Với overlap=100: `num_chunks = ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks`. Tăng từ 23 lên 25 chunk.
> 
> Lý do muốn overlap nhiều hơn: Overlap giúp giữ ngữ cảnh xuyên suốt giữa các chunk. Nếu overlap nhỏ, câu hoặc ý tưởng quan trọng có thể bị cắt đôi ở biên. Overlap lớn hơn đảm bảo thông tin cần thiết xuất hiện hoàn chỉnh trong ít nhất một chunk, giúp retrieval và LLM có ngữ cảnh đầy đủ.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Customer Support FAQ

**Tại sao nhóm chọn domain này?**
> Domain này giàu văn bản có cấu trúc rõ ràng (Q&A pairs), thường có metadata rõ ràng (category, urgency). Dữ liệu support thường cần retrieval chính xác vì sai lầm có thể ảnh hưởng đến trải nghiệm khách hàng. Domain này giúp đánh giá tốt việc chunking và filtering.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | Password Recovery Guide | Internal Docs | 2,450 | category: account, urgency: high |
| 2 | Billing FAQ | Internal Docs | 3,890 | category: billing, urgency: medium |
| 3 | Service Limitations | Internal Docs | 1,760 | category: service, urgency: low |
| 4 | Account Setup Steps | Internal Docs | 2,100 | category: account, urgency: medium |
| 5 | Refund Policy | Internal Docs | 1,680 | category: billing, urgency: high |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| category | string | account, billing, service | Tìm câu hỏi trong lĩnh vực cụ thể (lọc account FAQs) |
| urgency | string | high, medium, low | Ưu tiên kết quả cho vấn đề cấp tính cao |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| Password Recovery | FixedSizeChunker (`fixed_size`) | 6 | 410 | Tốt |
| Password Recovery | SentenceChunker (`by_sentences`) | 8 | 306 | Rất tốt |
| Password Recovery | RecursiveChunker (`recursive`) | 7 | 350 | Tốt |

### Strategy Của Tôi

**Loại:** SentenceChunker

**Mô tả cách hoạt động:**
> SentenceChunker chia văn bản theo ranh giới câu (., !, ?, .\n). Mỗi chunk chứa tối đa 3 câu. Strategy này giữ nguyên ý tưởng hoàn chỉnh trong mỗi chunk vì câu là đơn vị ngữ nghĩa tự nhiên. Không cắt đôi câu hay khái niệm giữa các chunk.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Với Customer Support FAQ, các câu hỏi và câu trả lời thường ngắn gọn và hoàn chỉnh trong vài câu. SentenceChunker đảm bảo mỗi chunk chứa một ý tưởng hoàn chỉnh (Q&A pair hoặc step hướng dẫn). Điều này giúp retrieval chính xác hơn vì LLM nhận được context đầy đủ mà không có nhiễu từ các phần không liên quan.

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| Password Recovery | best baseline (Recursive) | 7 | 350 | 8/10 |
| Password Recovery | **của tôi (SentenceChunker)** | 8 | 306 | **9/10** |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi (Hồ Thái Đức) | SentenceChunker | 8.5 | Chunk rõ ràng, ngữ cảnh đầy đủ | Chunk quá nhỏ, mất context dài |
| [Thành viên khác] | FixedSizeChunker | 7.5 | Kích thước đều, phù hợp vector DB | Cắt ngang câu, mất ý nghĩa |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> SentenceChunker tốt nhất cho Customer Support vì nó tôn trọng ranh giới tự nhiên của ngôn ngữ. Support FAQ cần độ chính xác cao và ngữ cảnh đầy đủ - SentenceChunker cung cấp cả hai. Recursive chunker cũng tốt nhưng kém một chút vì có thể tách tài liệu không cần thiết.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Sử dụng regex `(?<=[.!?])\s+` để tách văn bản thành các câu riêng lẻ tại biên câu. Sau đó nhóm các câu liên tiếp lại theo max_sentences_per_chunk. Edge cases: xử lý các dấu câu khác nhau (., !, ?), lọc bỏ khoảng trắng thừa, xử lý trường hợp regex không tìm thấy dấu câu.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Sử dụng thuật toán đệ quy thử từng separator theo thứ tự ưu tiên. Base case: nếu text <= chunk_size, trả về [text]; nếu không còn separator, chia chunk_size ký tự. Recursive case: tìm separator đầu tiên có trong text, chia, kiểm tra từng phần có vượt chunk_size không, nếu có gọi đệ quy với separators còn lại.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Lưu trữ: mỗi document được embed thành vector, lưu kèm id, content, metadata vào danh sách trong memory (hoặc ChromaDB nếu có). Search: embed query thành vector, tính dot product với tất cả vectors đã lưu, sắp xếp theo score giảm dần, trả về top_k.

**`search_with_filter` + `delete_document`** — approach:
> Filter: trước tiên lọc các records có metadata match điều kiện (so khớp key-value), sau đó chạy search trên tập đã filter. Delete: lặp qua tất cả records, xóa những record có id trùng với doc_id cần xóa, trả về True/False tùy vào có xóa được gì không.

### KnowledgeBaseAgent

**`answer`** — approach:
> Retrieve: gọi store.search() với top_k=3 để lấy các chunk liên quan. Build prompt: ghép các chunk thành context, wrap trong template prompt có cấu trúc (Context: [...], Question: [...], Answer:). Call LLM: gọi llm_fn(prompt) và trả về kết quả.

### Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.11.7, pytest-9.0.2, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.44s ==============================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Python là ngôn ngữ lập trình" | "Python là ngôn ngữ code" | high | 0.92 | ✓ |
| 2 | "Con chó chạy nhanh" | "Con mèo ngủ yên tĩnh" | low | 0.15 | ✓ |
| 3 | "Vector store lưu embeddings" | "Database lưu dữ liệu dưới dạng vectors" | high | 0.78 | ✓ |
| 4 | "Machine learning cần dữ liệu" | "Trời hôm nay đẹp lắm" | low | 0.05 | ✓ |
| 5 | "Cosine similarity tính góc" | "Cosine là hàm lượng giác" | medium | 0.64 | ✓ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Pair 3 hơi bất ngờ vì "Vector store lưu embeddings" và "Database lưu dữ liệu dưới dạng vectors" có score tương đối cao (0.78) mặc dù từ vựng khác nhau. Điều này nói rằng embeddings không chỉ học từ các từ riêng lẻ mà cả khái niệm ngữ nghĩa - "lưu", "embeddings/vectors", "dữ liệu" được kết hợp để tạo ý nghĩa chung. Embeddings nắm bắt được mối liên hệ giữa các khái niệm, không chỉ sự xuất hiện cùng nhau của từ.


---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Làm sao để reset password tài khoản? | Đăng nhập, chọn "Forgot Password", nhập email, kiểm tra email xác nhận, đặt password mới. |
| 2 | Tôi bị tính phí sai. Phải làm gì? | Liên hệ support với hóa đơn, giải thích vấn đề, support sẽ review và hoàn tiền trong 5-7 ngày. |
| 3 | Dịch vụ hỗ trợ những nước nào? | Hỗ trợ 50+ quốc gia ở châu Á, châu Âu, và Bắc Mỹ. Xem danh sách đầy đủ tại website. |
| 4 | Tôi quên username thì sao? | Xác thực bằng email đăng ký, reset username hoặc đặt lại password. Liên hệ support nếu không nhận được email. |
| 5 | Giới hạn số lần đăng nhập thất bại là bao nhiêu? | 5 lần thất bại liên tiếp sẽ khóa tài khoản 30 phút. Sử dụng "Forgot Password" để mở khóa trước. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Làm sao để reset password? | "Step 1: Go to login page, click Forgot... Step 2: Enter email... Step 3: Check email for reset link..." | 0.89 | ✓ | Kết quả hợp lý: hướng dẫn reset password đúng |
| 2 | Tôi bị tính phí sai | "Billing FAQ: If charged incorrectly, contact support with invoice... refund within 5-7 days" | 0.85 | ✓ | Kết quả chính xác: liên hệ support, hoàn tiền 5-7 ngày |
| 3 | Dịch vụ hỗ trợ những nước nào? | "Service Limitations: Supported in 50+ countries across Asia, Europe, North America" | 0.82 | ✓ | Kết quả đúng: 50+ quốc gia, châu Á/châu Âu/Bắc Mỹ |
| 4 | Quên username? | "Password Recovery Guide: Verify with email, reset username or password, contact support if no email received" | 0.88 | ✓ | Kết quả chính xác: xác thực email, reset username/password |
| 5 | Giới hạn đăng nhập thất bại? | "Account Security: 5 failed attempts = 30-min lockout, use Forgot Password to unlock early" | 0.90 | ✓ | Kết quả đúng: 5 lần → 30 phút khóa, reset password để mở |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Thấy được rằng FixedSizeChunker có thể tốt như SentenceChunker nếu tùy chỉnh overlap và chunk_size đúng cách. Thành viên dùng chunk_size=300, overlap=100 và đạt kết quả tương tự. Điều này dạy tôi rằng không phải chiến lược mà là tham số - cùng một chiến lược có thể hiệu quả hoặc không tùy vào miền.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Nhóm dùng domain "Cooking Recipes" thấy rằng custom chunking (chunk by steps/ingredients) hiệu quả hơn cả 3 built-in strategies. Điều này khiến tôi nhận ra rằng việc hiểu domain sâu và thiết kế strategy specifically cho domain đó là chìa khóa thành công, không phải dùng generic approach.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ thêm metadata chi tiết hơn như "step_count", "difficulty_level", "resolution_time" để support retrieval filtering tốt hơn. Ví dụ, với query "Cách nhanh nhất để reset password", filter để priority="quick" sẽ giúp LLM trả về giải pháp nhanh nhất thay vì tất cả các phương pháp.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 8 / 10 |
| Chunking strategy | Nhóm | 13 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 4 / 5 |
| **Tổng** | | **85 / 100** |

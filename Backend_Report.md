# Báo cáo Chương Backend

## 1. Giới thiệu chương

### 1.1. Phạm vi và mục tiêu của phần backend trong dự án

Chương này trình bày toàn bộ phần backend của dự án Data Mining về xu hướng công nghệ và thị trường tuyển dụng. Phạm vi của chương xoay quanh ba khối công việc chính: xây dựng API service trung tâm bằng Golang để phục vụ frontend, phát triển một số API bổ trợ bên trong các service AI viết bằng Python tại `ai-rag-core` và `ml-clustering`, và đóng gói toàn bộ hệ thống bằng Docker nhằm bảo đảm tính đồng nhất giữa môi trường phát triển và môi trường vận hành.

Mục tiêu của phần backend không chỉ dừng ở việc cung cấp các endpoint cho frontend, mà còn phải đảm nhiệm vai trò điều phối giữa các service: tiếp nhận yêu cầu từ phía người dùng, thực hiện xác thực, truy vấn cơ sở dữ liệu nghiệp vụ, gọi sang các service AI khi cần xử lý ngôn ngữ tự nhiên hoặc phân cụm dữ liệu, sau đó tổng hợp và trả kết quả về cho frontend. Trên cơ sở đó, hệ thống backend cần đáp ứng được bốn yêu cầu cốt lõi: tính đúng đắn của dữ liệu trả về, khả năng mở rộng theo từng thành phần một cách độc lập, độ an toàn của thông tin người dùng, và sự thuận tiện trong triển khai.

Cụ thể hơn, các nội dung được trình bày trong chương bao gồm: kiến trúc tổng thể của hệ thống và cách phân chia trách nhiệm giữa các service; thiết kế API theo chuẩn REST cùng với mô hình DTO; cơ chế bảo mật bằng JWT và băm mật khẩu; tầng dữ liệu với PostgreSQL cho dữ liệu nghiệp vụ và Neo4j cho dữ liệu dạng đồ thị; cuối cùng là quy trình đóng gói, triển khai bằng Docker và Docker Compose. Những nội dung liên quan trực tiếp đến mô hình học máy, pipeline huấn luyện hoặc logic RAG nội bộ sẽ được trình bày ở các chương khác của báo cáo; trong phạm vi chương này, các service AI chỉ được đề cập ở mức giao diện mà backend tương tác.

### 1.2. Vai trò của backend trong pipeline Data Mining

Trong toàn bộ pipeline của dự án, backend đóng vai trò là tầng trung gian giữa người dùng cuối và các thành phần xử lý dữ liệu. Pipeline có thể được mô tả tóm tắt như sau: dữ liệu thô về thị trường tuyển dụng và xu hướng công nghệ được thu thập và tiền xử lý ở các pipeline riêng, sau đó được nạp vào PostgreSQL và Neo4j; song song với đó, các service AI nạp mô hình và sẵn sàng phục vụ inference. Khi người dùng tương tác với ứng dụng, mọi yêu cầu đều đi vào Golang API service trước, rồi từ đây mới được phân luồng tới các thành phần phía sau.

Vai trò điều phối này được thể hiện rõ ở các luồng nghiệp vụ tiêu biểu. Ở luồng chatbot, Golang tiếp nhận tin nhắn của người dùng, xác thực JWT, lưu tin nhắn vào lịch sử hội thoại trong PostgreSQL, sau đó gọi sang service RAG tại `ai-rag-core` để sinh phản hồi, đồng thời sử dụng Server-Sent Events để stream nội dung trả lời về phía frontend theo thời gian thực. Ở luồng so sánh công nghệ, Golang truy vấn số liệu thống kê từ cơ sở dữ liệu, gọi tiếp sang service AI để sinh tóm tắt bằng mô hình ngôn ngữ lớn, rồi đóng gói kết quả trong một response duy nhất gửi về frontend. Ở luồng phân cụm và khám phá đồ thị quan hệ giữa các công nghệ, Golang kết hợp dữ liệu phân cụm từ `ml-clustering` với dữ liệu đồ thị trong Neo4j để dựng nên cấu trúc trả về cho client.

Một nguyên tắc xuyên suốt được nhóm tuân thủ trong thiết kế là frontend chỉ giao tiếp trực tiếp với Golang, còn các service Python được giữ ở mạng nội bộ và chỉ chấp nhận yêu cầu đến từ Golang. Cách phân tầng này giúp tập trung logic xác thực và kiểm soát truy cập tại một điểm duy nhất, giảm bề mặt tấn công, đồng thời cho phép các service AI tập trung vào nhiệm vụ chuyên biệt mà không phải gánh thêm phần xử lý nghiệp vụ chung.

### 1.3. Tổng quan công nghệ sử dụng

Phần backend được xây dựng trên một bộ công nghệ được lựa chọn nhằm cân bằng giữa hiệu năng, tốc độ phát triển và khả năng triển khai. Service chính viết bằng Go phiên bản 1.25 sử dụng framework Gin để định tuyến HTTP và xử lý middleware, kết hợp với thư viện `golang-jwt` cho phần xác thực, `pgx` để giao tiếp trực tiếp với PostgreSQL theo hướng repository, và driver chính thức của Neo4j cho các truy vấn đồ thị. Tài liệu API được sinh tự động bằng `swaggo/swag` và phục vụ qua giao diện Swagger UI, giúp việc kiểm thử cũng như phối hợp với frontend trở nên thuận lợi. Cấu hình ứng dụng được nạp từ file môi trường thông qua `godotenv`, qua đó toàn bộ thông tin nhạy cảm như khoá ký JWT, chuỗi kết nối cơ sở dữ liệu và endpoint của các service AI đều được tách khỏi mã nguồn.

Các service AI viết bằng Python được tổ chức thành hai thư mục độc lập. Thư mục `ai-rag-core` chịu trách nhiệm cho pipeline RAG, kèm theo MLflow để theo dõi thử nghiệm và quản lý mô hình. Thư mục `ml-clustering` quản lý pipeline phân cụm dữ liệu bằng DVC, với tham số được khai báo trong `params.yaml` và các bước thực thi được mô tả trong `dvc.yaml`. Cả hai service đều được bọc bằng một lớp API HTTP để Golang có thể gọi tới theo cùng một quy ước thống nhất.

Ở tầng dữ liệu, hệ thống sử dụng PostgreSQL làm cơ sở dữ liệu nghiệp vụ chính, lưu trữ thông tin người dùng, lịch sử hội thoại và các bảng thống kê phục vụ dashboard. Neo4j được dùng cho phần dữ liệu có cấu trúc đồ thị, nơi quan hệ giữa các thực thể như công nghệ, ngành nghề và mức lương được khai thác bằng các truy vấn Cypher.

Về phần đóng gói và vận hành, mỗi service đều có Dockerfile riêng, trong đó image của Golang được xây dựng theo cơ chế multi-stage nhằm giữ image cuối ở kích thước nhỏ và không kèm theo công cụ build. Docker Compose được sử dụng để mô tả toàn bộ hệ thống ở mức môi trường phát triển, bao gồm Golang API, các service Python, PostgreSQL, Neo4j cùng với mạng nội bộ và các volume cần thiết, qua đó cho phép khởi chạy toàn bộ stack chỉ bằng một lệnh duy nhất.

---

## 2. Kiến trúc hệ thống

### 2.1. Tổng quan kiến trúc

Hệ thống backend được thiết kế theo mô hình microservices có phân tầng rõ ràng, trong đó Golang API service đóng vai trò là cổng vào duy nhất của toàn bộ phía server, còn các service AI viết bằng Python được đặt ở tầng phía sau như những thành phần chuyên biệt phục vụ nhu cầu inference. Mọi yêu cầu phát sinh từ phía client, dù là tin nhắn chatbot, truy vấn so sánh công nghệ hay yêu cầu khám phá đồ thị quan hệ, đều đi qua Golang API service trước khi được phân luồng tới các thành phần phía sau.

Sơ đồ kiến trúc tổng thể có thể được mô tả như sau:

```
                ┌────────────────────────────────────────────────┐
                │              Client (Web Frontend)             │
                └──────────────────────┬─────────────────────────┘
                                       │ HTTPS  (REST + SSE)
                                       ▼
                ┌────────────────────────────────────────────────┐
                │       Golang API Service  (Gin, /api/v1)       │
                │  Auth · Radar · Compare · Graph · Chat · Admin │
                │       JWT middleware · CORS · Analytics        │
                └─────────┬──────────────────────────┬───────────┘
                          │ SQL (pgx)                │ Cypher
                          ▼                          ▼
                ┌──────────────────┐        ┌──────────────────┐
                │   PostgreSQL     │        │      Neo4j       │
                │ users, chat_*,   │        │  graph data:     │
                │ analytics, ...   │        │  tech, job, …    │
                └──────────────────┘        └──────────────────┘
                          ▲
                          │ internal HTTP  (REST + SSE)
                          ▼
        ┌─────────────────────────────────────────────────────────┐
        │            Python AI Services (mạng nội bộ)             │
        │  ┌───────────────────────┐   ┌───────────────────────┐  │
        │  │     ai-rag-core       │   │     ml-clustering     │  │
        │  │  RAG pipeline, LLM,   │   │  pipeline phân cụm,   │  │
        │  │  MLflow tracking      │   │  DVC, params.yaml     │  │
        │  └───────────────────────┘   └───────────────────────┘  │
        └─────────────────────────────────────────────────────────┘
```

Sơ đồ trên phản ánh hai nguyên tắc cốt lõi của thiết kế. Thứ nhất, frontend không được phép trực tiếp kết nối đến bất kỳ service Python nào; toàn bộ luồng giao tiếp với phía AI đều phải đi qua Golang. Thứ hai, dữ liệu nghiệp vụ được tách rõ giữa hai loại: dữ liệu quan hệ thông thường nằm trên PostgreSQL, còn dữ liệu có cấu trúc đồ thị nằm trên Neo4j; Golang là thành phần duy nhất sở hữu quyền đọc và ghi vào cả hai cơ sở dữ liệu này, qua đó tập trung toàn bộ logic kiểm soát truy cập và toàn vẹn dữ liệu về một điểm.

### 2.2. Các thành phần chính và trách nhiệm

#### 2.2.1. Golang API service

Golang API service là thành phần trung tâm của backend, được tổ chức theo kiến trúc phân lớp gồm router, handler, service và repository. Toàn bộ endpoint công khai đều được nhóm dưới tiền tố `/api/v1` và được chia thành các nhóm chức năng tương ứng với từng domain nghiệp vụ: nhóm `auth` xử lý đăng ký, đăng nhập, làm mới token và lấy thông tin người dùng hiện tại; nhóm `radar` cung cấp số liệu xu hướng công nghệ phục vụ cho biểu đồ radar và bảng xếp hạng; nhóm `compare` đảm nhiệm việc so sánh các công nghệ và sinh tóm tắt bằng mô hình ngôn ngữ; nhóm `graph` phụ trách các truy vấn khám phá đồ thị quan hệ; nhóm `chat` quản lý session hội thoại với chatbot; và nhóm `admin` cung cấp các chức năng quản trị cùng các thống kê dashboard.

Bên cạnh logic nghiệp vụ, Golang API còn đảm nhiệm các tác vụ xuyên suốt thông qua hệ thống middleware: kiểm tra JWT cho các endpoint yêu cầu xác thực, kiểm tra quyền quản trị cho nhóm endpoint admin, ghi nhận sự kiện truy cập để phục vụ analytics, kiểm tra cờ bảo trì hệ thống, cũng như kiểm tra cờ bật/tắt tính năng đối với các module có thể được điều chỉnh động như chat và graph. Phần cấu hình CORS được khai báo tập trung tại router, cho phép kiểm soát chặt chẽ các origin được phép truy cập, các header được expose và phương thức HTTP được chấp nhận. Ngoài ra, service này còn cung cấp tài liệu API tương tác qua Swagger UI tại đường dẫn `/swagger`, cùng với endpoint `/health` để phục vụ kiểm tra trạng thái khi triển khai.

#### 2.2.2. Service ai-rag-core

Service `ai-rag-core` là thành phần phụ trách toàn bộ pipeline Retrieval-Augmented Generation, được xây dựng bằng Python và bọc bởi một lớp API HTTP để Golang có thể gọi tới. Service này tiếp nhận truy vấn từ Golang, thực hiện việc trích xuất ngữ cảnh liên quan từ kho tri thức, sau đó tổng hợp prompt và gọi tới mô hình ngôn ngữ để sinh phản hồi. Ngoài endpoint chính phục vụ chat, service còn cung cấp endpoint dạng streaming dựa trên Server-Sent Events nhằm hỗ trợ trải nghiệm trả lời theo thời gian thực, cùng với endpoint `/health` để kiểm tra trạng thái kết nối tới Neo4j và phiên bản đang chạy. MLflow được tích hợp để theo dõi các thử nghiệm prompt và quản lý các phiên bản mô hình được sử dụng.

#### 2.2.3. Service ml-clustering

Service `ml-clustering` chịu trách nhiệm cho pipeline phân cụm dữ liệu liên quan đến công nghệ và thị trường tuyển dụng. Pipeline được quản lý bằng DVC, với toàn bộ tham số đầu vào khai báo trong `params.yaml` và các bước thực thi mô tả trong `dvc.yaml`, nhờ đó việc tái lập kết quả giữa các lần chạy được bảo đảm. Kết quả phân cụm sau khi xử lý sẽ được lưu trữ hoặc tái xuất dưới dạng API HTTP để Golang truy xuất khi cần. Việc tách riêng pipeline phân cụm khỏi service RAG giúp cô lập hai loại workload có đặc tính rất khác nhau: một bên là tác vụ inference theo yêu cầu với thời gian phản hồi ngắn, một bên là tác vụ tính toán theo lô có chu kỳ chạy độc lập.

#### 2.2.4. Tầng lưu trữ dữ liệu

Hệ thống sử dụng hai loại cơ sở dữ liệu chuyên biệt nhằm phù hợp với đặc trưng của từng loại dữ liệu. PostgreSQL là cơ sở dữ liệu nghiệp vụ chính, lưu trữ thông tin người dùng, hồ sơ cá nhân, các bảng liên quan đến session và tin nhắn của chatbot, các bảng phục vụ thống kê analytics cũng như các thiết lập cấu hình hệ thống có thể được điều chỉnh tại thời điểm vận hành. Toàn bộ truy cập tới PostgreSQL được thực hiện qua thư viện `pgx` và được đóng gói trong các repository tương ứng với từng nhóm bảng, qua đó tách rời tầng logic nghiệp vụ khỏi chi tiết truy vấn SQL.

Neo4j được sử dụng cho phần dữ liệu có bản chất là đồ thị quan hệ, bao gồm các thực thể như công nghệ, ngành nghề, kỹ năng, mức lương và địa điểm cùng các mối liên kết giữa chúng. Cấu trúc dữ liệu này phục vụ trực tiếp cho ba nhóm chức năng quan trọng của hệ thống là radar, compare và graph. Tương tự PostgreSQL, các truy vấn Cypher tới Neo4j cũng được đóng gói trong các repository chuyên biệt nhằm đảm bảo tính nhất quán và khả năng tái sử dụng.

### 2.3. Luồng dữ liệu tiêu biểu

Để minh hoạ cách các thành phần tương tác với nhau, phần này trình bày hai luồng nghiệp vụ tiêu biểu của hệ thống.

#### 2.3.1. Luồng chatbot có streaming

Luồng chatbot là luồng phức tạp nhất trong toàn bộ hệ thống, do có sự tham gia của cả Golang, service RAG, PostgreSQL và cơ chế streaming hai chặng. Khi người dùng gửi một câu hỏi mới trong một session đang mở, trình tự xử lý diễn ra như sau:

```
Frontend                Golang API           ai-rag-core         PostgreSQL
   │                         │                    │                  │
   │  POST /chat/session/{id}/messages/stream     │                  │
   │────────────────────────►│                    │                  │
   │                         │   verify JWT       │                  │
   │                         │   check session    │                  │
   │                         │──────────────────────────────────────►│
   │                         │◄──────────────────────────────────────│
   │                         │                                       │
   │                         │   POST /chat/stream (SSE)             │
   │                         │───────────────────►│                  │
   │                         │                    │  retrieve docs   │
   │                         │                    │  build prompt    │
   │                         │                    │  call LLM        │
   │                         │◄── SSE frames ─────│                  │
   │◄── forward SSE frames ──│                    │                  │
   │                         │                                       │
   │                         │   persist assistant message           │
   │                         │──────────────────────────────────────►│
```

Ở chặng đầu tiên, Golang xác thực JWT của người dùng, kiểm tra quyền truy cập session, sau đó mở một kết nối HTTP tới endpoint streaming của service RAG và truyền câu truy vấn cùng định danh session. Ở chặng thứ hai, service RAG thực hiện tìm kiếm ngữ cảnh liên quan, dựng prompt và phát các SSE frame tương ứng với từng phần của câu trả lời. Golang đóng vai trò proxy, chuyển tiếp từng frame về cho frontend gần như tức thời nhờ cơ chế flush sau mỗi blank line. Khi luồng kết thúc, Golang lưu lại tin nhắn của trợ lý vào bảng tin nhắn trong PostgreSQL để bảo đảm tính bền vững của lịch sử hội thoại.

#### 2.3.2. Luồng so sánh công nghệ kèm tóm tắt LLM

Luồng so sánh công nghệ minh hoạ trường hợp Golang phải tổng hợp dữ liệu từ Neo4j rồi kết hợp với kết quả sinh ra từ service AI. Khi người dùng yêu cầu một bản tóm tắt so sánh giữa các công nghệ, Golang thực hiện các truy vấn Cypher trên Neo4j để lấy số liệu thống kê, đóng gói các số liệu này thành payload theo cấu trúc đã thống nhất với service RAG, sau đó gửi yêu cầu sang phía Python để sinh tóm tắt. Kết quả tóm tắt được Golang gói chung với số liệu thống kê trong một response duy nhất trả về cho frontend, nhờ đó frontend không cần thực hiện hai lượt gọi riêng rẽ và độ trễ tổng thể được giảm thiểu.

### 2.4. Lý do lựa chọn kiến trúc microservices

Việc lựa chọn kiến trúc microservices thay vì kiến trúc nguyên khối được cân nhắc dựa trên đặc trưng nội tại của dự án. Hệ thống vừa phải phục vụ các yêu cầu CRUD và truy vấn dữ liệu nghiệp vụ thông thường, vừa phải đảm nhiệm các tác vụ học máy với yêu cầu hoàn toàn khác biệt về tài nguyên, môi trường thực thi và chu kỳ phát hành. Nếu gộp toàn bộ vào một dịch vụ duy nhất, hai loại workload này sẽ ràng buộc lẫn nhau ở cả tầng triển khai lẫn tầng phụ thuộc thư viện, gây khó khăn khi mở rộng và bảo trì.

Lợi ích đầu tiên của việc tách dịch vụ là khả năng mở rộng độc lập. Trong các luồng có hoạt động AI dày đặc, chỉ phần dịch vụ Python cần được nhân bản để đáp ứng nhu cầu inference, trong khi Golang API vẫn có thể giữ nguyên số lượng instance. Ngược lại, khi lưu lượng truy cập dashboard tăng cao, có thể mở rộng riêng Golang mà không cần can thiệp tới các service AI. Lợi ích thứ hai là sự tách biệt về công nghệ và môi trường: Golang được lựa chọn cho tầng API nhờ hiệu năng, mô hình concurrency nhẹ và khả năng biên dịch ra binary tĩnh thuận lợi cho việc đóng gói container; Python được lựa chọn cho tầng AI vì hệ sinh thái thư viện học máy phong phú và sự gần gũi với pipeline huấn luyện hiện hữu. Mỗi service có thể chọn thư viện và phiên bản phù hợp mà không gây xung đột với phần còn lại.

Lợi ích thứ ba là khả năng cô lập sự cố. Khi một mô hình AI gặp lỗi hoặc một pipeline học máy bị treo, các chức năng không phụ thuộc vào AI như xác thực, quản lý người dùng hay xem dashboard vẫn hoạt động bình thường nhờ vào hệ thống cờ tính năng được tích hợp trong Golang. Cuối cùng, kiến trúc microservices tạo điều kiện thuận lợi cho việc phân chia công việc giữa các thành viên trong nhóm và cho phép triển khai từng dịch vụ một cách độc lập, qua đó rút ngắn chu kỳ phát hành và giảm rủi ro mỗi lần đưa thay đổi lên môi trường vận hành.

Mặt trái của kiến trúc này nằm ở chi phí điều phối giữa các service và yêu cầu cao hơn về quan sát hệ thống. Để giảm thiểu các hạn chế đó, nhóm đã thống nhất một số quy ước trong giao tiếp nội bộ: sử dụng REST cho mọi luồng tương tác để tránh phụ thuộc vào hạ tầng message queue ở giai đoạn đầu, áp dụng timeout rõ ràng cho từng lời gọi từ Golang sang Python, đồng thời chuẩn hoá hợp đồng dữ liệu giữa hai bên thông qua các DTO được mô tả ngay tại tầng client trong mã nguồn Go. Khi hệ thống mở rộng và nhu cầu giao tiếp giữa các service tăng cao, gRPC và message queue sẽ được cân nhắc bổ sung như đã đề cập trong phần kết luận chương.

## 3. Microservices: Go và Python

### 3.1. Phân chia service và nguyên tắc tách

Việc phân chia hệ thống thành các service riêng biệt được thực hiện dựa trên hai trục: phân chia theo bounded context của nghiệp vụ và phân chia theo đặc tính workload của từng nhóm tác vụ. Cách kết hợp này nhằm bảo đảm mỗi service có một trách nhiệm duy nhất, dễ hiểu và có thể tiến hoá độc lập mà không kéo theo các thành phần khác phải thay đổi.

Trên trục bounded context, toàn bộ logic nghiệp vụ liên quan đến người dùng, xác thực, quyền truy cập, lịch sử hội thoại, cấu hình hệ thống và các thống kê dashboard đều được tập trung tại Golang API service. Đây là vùng dữ liệu có ràng buộc giao dịch chặt chẽ với PostgreSQL, đồng thời cũng là nơi áp dụng các quy tắc bảo mật xuyên suốt. Ngược lại, các tác vụ thuộc bounded context của trí tuệ nhân tạo, bao gồm sinh phản hồi bằng mô hình ngôn ngữ lớn, trích xuất thực thể, tìm kiếm ngữ cảnh và phân cụm công nghệ, được tách hoàn toàn sang phía các service Python.

Trên trục đặc tính workload, mỗi service được tách dựa trên yêu cầu khác biệt về tài nguyên và chu kỳ thực thi. Golang API service xử lý các yêu cầu HTTP có độ trễ thấp và đồng thời cao, phù hợp với mô hình concurrency dựa trên goroutine. Service `ai-rag-core` xử lý các tác vụ inference theo yêu cầu, có nhu cầu lớn về bộ nhớ để nạp mô hình embedding, mô hình reranker và mô hình NER vào RAM ngay từ thời điểm khởi động. Service `ml-clustering` lại phục vụ một loại workload hoàn toàn khác là tính toán theo lô, nơi pipeline phân cụm được chạy định kỳ và kết quả được snapshot dưới dạng artifact để API tra cứu lại sau này. Việc đặt ba loại workload này vào ba container độc lập cho phép cấp phát tài nguyên một cách chính xác, tránh hiện tượng một workload nặng gây ảnh hưởng đến độ trễ của các luồng còn lại.

Nguyên tắc bao trùm khi phân tách là Golang giữ vai trò chủ thể duy nhất sở hữu dữ liệu nghiệp vụ và là điểm vào duy nhất từ phía client; các service Python chỉ phục vụ inference và không có cơ sở dữ liệu nghiệp vụ riêng. Khi cần lưu trữ ngữ cảnh hội thoại có thời gian sống dài, dữ liệu được đẩy về phía Golang để ghi vào PostgreSQL, qua đó tránh tình trạng dữ liệu nghiệp vụ bị phân mảnh ở nhiều nơi.

### 3.2. Golang API service

#### 3.2.1. Cấu trúc thư mục

Mã nguồn của Golang API service được tổ chức theo kiến trúc phân lớp theo quy ước phổ biến trong cộng đồng Go, với toàn bộ logic nội bộ được đặt dưới thư mục `internal` để ngăn các module bên ngoài import nhầm. Cấu trúc tổng quan như sau:

```
golang-api/
├── cmd/
│   └── api/                    # entrypoint, bootstrap HTTP server
├── internal/
│   ├── config/                 # nạp biến môi trường, cấu hình ứng dụng
│   ├── database/               # khởi tạo connection pool Postgres & Neo4j
│   ├── domain/                 # entity / model nghiệp vụ
│   ├── dto/                    # request/response DTO
│   ├── middleware/             # JWT, CORS, analytics, maintenance, feature flag
│   ├── handler/                # tầng HTTP, parse request, gọi service
│   ├── service/                # tầng business logic, gồm cả ai_client
│   ├── repository/
│   │   ├── postgres/           # repository SQL trên PostgreSQL
│   │   └── neo4jrepo/          # repository Cypher trên Neo4j
│   ├── router/                 # mount routes /api/v1
│   └── sse/                    # helper cho Server-Sent Events
├── migrations/                 # file SQL migration
├── docs/                       # tài liệu Swagger sinh tự động
├── Dockerfile
├── go.mod
└── go.sum
```

Kiến trúc này phản ánh nguyên tắc tách riêng các mối quan tâm. Tầng handler chỉ đảm nhiệm việc phân tích yêu cầu, gọi sang tầng service và đóng gói response, không chứa logic nghiệp vụ. Tầng service tập trung toàn bộ logic xử lý, đồng thời là nơi gọi xuống tầng repository hoặc gọi sang client của service AI. Tầng repository cô lập các chi tiết của cơ sở dữ liệu, cho phép thay đổi cách truy vấn mà không ảnh hưởng đến phần còn lại của hệ thống. Các DTO được khai báo riêng nhằm tách biệt cấu trúc dữ liệu trao đổi với client khỏi entity nghiệp vụ, một nội dung sẽ được phân tích kỹ hơn trong chương về thiết kế API.

#### 3.2.2. Framework và thư viện sử dụng

Framework HTTP được lựa chọn là Gin do tốc độ xử lý route nhanh, hệ sinh thái middleware phong phú và cú pháp đơn giản. Việc bắt buộc xác thực JWT trên các endpoint nhạy cảm được thực hiện qua middleware tuỳ chỉnh dựa trên thư viện `golang-jwt/jwt/v5`. Đối với truy cập PostgreSQL, dự án sử dụng `jackc/pgx/v5` thay vì các ORM truyền thống nhằm giữ toàn quyền kiểm soát câu truy vấn SQL và đạt hiệu năng cao hơn, đặc biệt khi xử lý các bảng analytics có lượng dữ liệu lớn. Đối với Neo4j, driver chính thức `neo4j-go-driver/v5` được dùng để thực thi các câu truy vấn Cypher từ tầng repository. Cấu hình ứng dụng được nạp từ file môi trường thông qua `joho/godotenv`, cho phép tách hoàn toàn các giá trị nhạy cảm như khoá ký JWT, chuỗi kết nối cơ sở dữ liệu và endpoint của service AI khỏi mã nguồn. Phần CORS được khai báo qua `gin-contrib/cors` với danh sách origin được nạp từ biến môi trường, đồng thời cho phép gửi credentials cùng các header cần thiết cho phía frontend.

#### 3.2.3. Swagger và tài liệu API

Tài liệu API được sinh tự động từ chú thích godoc trong mã nguồn thông qua công cụ `swaggo/swag`. Mỗi handler được mô tả bằng các thẻ `@Summary`, `@Tags`, `@Param`, `@Success` và `@Router`, từ đó công cụ sinh ra các tệp `docs.go`, `swagger.json` và `swagger.yaml` đặt trong thư mục `docs`. Service Golang nhúng giao diện Swagger UI tại đường dẫn `/swagger/*any` thông qua `swaggo/gin-swagger`, cho phép kiểm thử trực tiếp các endpoint ngay trên trình duyệt. Nhờ tài liệu được sinh từ chính mã nguồn, sự đồng bộ giữa tài liệu và hành vi thực tế của API luôn được bảo đảm sau mỗi lần build, qua đó loại bỏ các sai lệch thường gặp khi tài liệu được duy trì thủ công.

### 3.3. Các service Python

#### 3.3.1. Service ai-rag-core

Service `ai-rag-core` được xây dựng trên nền FastAPI, một framework Python hiện đại với hỗ trợ bất đồng bộ gốc, validation dữ liệu qua Pydantic và sinh tài liệu OpenAPI tương tự Swagger. Service được tổ chức thành nhiều module chuyên biệt nhằm tách rời các giai đoạn của pipeline RAG. Cấu trúc thư mục của service được rút gọn như sau:

```
ai-rag-core/app/
├── main.py                     # FastAPI app, lifespan, warm-up models
├── config.py
├── api/
│   ├── routes_chat.py          # /chat, /chat/stream, /chat/session/...
│   ├── routes_embed.py         # /embed
│   ├── routes_health.py        # /health
│   └── schemas.py              # Pydantic models cho request/response
├── core/
│   ├── embedder.py             # E5 embedding model
│   ├── reranker.py             # CrossEncoder rerank
│   ├── entity_extractor.py     # NER pipeline
│   ├── retriever.py            # truy xuất ngữ cảnh
│   ├── retriever_graph.py      # truy xuất qua Neo4j
│   ├── retriever_user.py       # truy xuất theo người dùng
│   ├── prompt_builder.py       # dựng prompt cho LLM
│   ├── generator.py            # sinh phản hồi non-stream
│   ├── generator_stream.py     # sinh phản hồi streaming
│   ├── pipeline.py             # ráp đầy đủ pipeline non-stream
│   └── pipeline_stream.py      # ráp đầy đủ pipeline stream
├── services/
│   └── chat_service.py
├── db/
│   ├── neo4j_client.py
│   └── postgres_client.py
├── models/
└── prompts/
```

Đặc điểm đáng chú ý là cơ chế warm-up mô hình ngay tại thời điểm khởi động. Trong hàm `lifespan` của FastAPI, các mô hình E5 embedding, CrossEncoder reranker và NER được nạp vào bộ nhớ thông qua thread pool nhằm tránh chặn event loop. Nhờ đó, ngay sau khi service sẵn sàng nhận yêu cầu, các tác vụ inference đầu tiên đã có thể chạy ở tốc độ tối đa mà không phải chịu chi phí khởi tạo mô hình theo từng yêu cầu. MLflow được tích hợp tại tầng pipeline để theo dõi các thử nghiệm liên quan đến prompt và quản lý các phiên bản mô hình, đồng thời lưu lại các chỉ số đánh giá phục vụ việc cải tiến chất lượng phản hồi theo thời gian. Ngoài thư mục `app`, kho mã của service còn chứa thư mục `scripts` phục vụ các tác vụ vận hành như tiền xử lý dữ liệu và đánh giá pipeline.

#### 3.3.2. Service ml-clustering

Service `ml-clustering` được xây dựng quanh hai khối tách biệt. Khối thứ nhất là pipeline tính toán, được quản lý bằng DVC với các bước thực thi mô tả trong `dvc.yaml`, tham số tập trung trong `params.yaml` và các artifact đầu ra như nhãn cụm và mapping công nghệ – cụm được lưu dưới dạng parquet. Pipeline kết hợp thuật toán phân cụm HDBSCAN với một bước gán nhãn ngữ nghĩa cho từng cụm thông qua mô hình ngôn ngữ lớn. Khối thứ hai là lớp API HTTP cũng được xây dựng bằng FastAPI, có nhiệm vụ nạp các artifact của lần chạy gần nhất vào bộ nhớ tại thời điểm khởi động thông qua đối tượng store, sau đó phục vụ các yêu cầu tra cứu của Golang API.

Các endpoint chính của service bao gồm `/health` để báo cáo trạng thái cùng thông tin snapshot hiện tại, `/clusters` để liệt kê toàn bộ cụm đã được gán nhãn, `/clusters/{cluster_id}` để truy xuất chi tiết của một cụm kèm danh sách thành viên, `/tech/{tech_name}/cluster` để xác định một công nghệ cụ thể thuộc cụm nào, và `/predict/batch` để tra cứu hàng loạt theo danh sách tên công nghệ. Mô hình tổ chức này tách rõ ràng giữa quá trình tính toán nặng diễn ra ngoại tuyến và quá trình phục vụ tra cứu trực tuyến, nhờ đó độ trễ tại runtime được giữ ở mức tối thiểu và việc cập nhật snapshot có thể được thực hiện mà không gián đoạn dịch vụ.

#### 3.3.3. Lớp API expose endpoint

Cả hai service Python đều thống nhất sử dụng FastAPI làm framework expose endpoint, lý do là FastAPI hỗ trợ async gốc, tự động sinh tài liệu OpenAPI và tích hợp Pydantic cho việc khai báo schema đầu vào, đầu ra một cách rõ ràng. Mọi schema được khai báo tập trung trong các module `schemas.py` của từng service, giúp việc đồng bộ hợp đồng dữ liệu với phía Golang trở nên thuận tiện: khi schema phía Python thay đổi, các DTO tương ứng ở tầng client trong mã nguồn Go sẽ được điều chỉnh theo đúng định dạng đã được tài liệu hoá.

### 3.4. Giao tiếp giữa các service

Tất cả các luồng giao tiếp giữa Golang và các service Python đều được thực hiện qua giao thức HTTP với hai biến thể: REST thông thường cho các yêu cầu request/response đồng bộ, và Server-Sent Events cho các luồng cần stream nội dung theo thời gian thực. Lựa chọn này dựa trên hai yếu tố: tính phổ dụng và dễ kiểm thử của HTTP, cùng với việc giảm thiểu chi phí hạ tầng ở giai đoạn đầu so với phương án sử dụng gRPC hay hệ thống message queue.

Payload trao đổi giữa hai bên được mã hoá dưới dạng JSON, với cấu trúc được thống nhất chặt chẽ thông qua hai tầng tài liệu hoá: phía Python sử dụng Pydantic schema còn phía Go khai báo các DTO tương ứng trong module `service/ai_client.go`. Cách làm này đảm bảo mọi trường dữ liệu đều có kiểu rõ ràng và mọi thay đổi đều có thể được phát hiện ngay tại thời điểm biên dịch hoặc kiểm thử.

Cơ chế xử lý timeout được phân biệt theo loại yêu cầu. Đối với các lời gọi không streaming, Golang sử dụng một `http.Client` với timeout 60 giây, đủ để các tác vụ sinh phản hồi không quá dài có thể hoàn tất nhưng vẫn ngăn được tình trạng treo vô hạn khi service phía sau gặp sự cố. Đối với các lời gọi streaming, một `http.Client` không đặt timeout được sử dụng riêng, nhằm cho phép phiên SSE có thể kéo dài tự nhiên theo độ dài câu trả lời từ mô hình ngôn ngữ; thay vào đó, việc huỷ luồng được kiểm soát thông qua context của request phía Gin, qua đó vẫn bảo đảm tài nguyên được giải phóng khi client đóng kết nối.

Hợp đồng lỗi giữa các service được chuẩn hoá theo quy ước HTTP. Khi service AI trả về mã trạng thái lớn hơn hoặc bằng 300, Golang đọc toàn bộ phần thân lỗi, đóng gói lại thành một thông điệp có ngữ cảnh kèm theo mã trạng thái gốc, sau đó phản hồi về frontend bằng mã `502 Bad Gateway`. Cách xử lý này cho phép phân biệt rõ ràng giữa lỗi nghiệp vụ phát sinh tại Golang và lỗi xảy ra do dịch vụ phụ thuộc, đồng thời giúp việc chẩn đoán sự cố trong môi trường vận hành trở nên thuận lợi hơn.

### 3.5. Cấu hình endpoint qua biến môi trường

Trong giai đoạn hiện tại, hệ thống chưa cần đến một cơ chế service discovery động kiểu Consul hay etcd; thay vào đó, địa chỉ của các service được cấu hình qua biến môi trường và được nạp tại thời điểm khởi tạo ứng dụng. Cụ thể, Golang đọc giá trị `PYTHON_AI_BASE_URL` từ biến môi trường để xác định điểm cuối của service RAG. Cách tiếp cận này có ba ưu điểm. Thứ nhất, cùng một image binary có thể được triển khai ở nhiều môi trường khác nhau chỉ bằng việc thay đổi tập biến môi trường, không cần phải biên dịch lại. Thứ hai, trong môi trường Docker Compose, tên service đóng vai trò như định danh DNS nội bộ, do đó việc cấu hình endpoint chỉ đơn giản là trỏ tới tên service tương ứng. Thứ ba, khi hệ thống được nâng cấp lên môi trường orchestration như Kubernetes, cùng cơ chế đó vẫn áp dụng được, chỉ thay tên DNS bằng tên service trong cluster mà không phải sửa đổi mã nguồn.

## 4. Thiết kế API

### 4.1. Quy ước RESTful

Toàn bộ API công khai của hệ thống được thiết kế bám sát các nguyên tắc của kiến trúc REST nhằm bảo đảm tính nhất quán, dễ dự đoán và thuận tiện cho phía frontend khi tích hợp. Mỗi nhóm chức năng được mô hình hoá quanh một tài nguyên cụ thể, và mọi thao tác trên tài nguyên đó đều được biểu diễn thông qua một tổ hợp định nghĩa rõ ràng giữa phương thức HTTP và đường dẫn.

Cách đặt tên tài nguyên tuân theo quy ước danh từ số nhiều và viết thường, các đoạn nhiều từ được nối bằng dấu gạch dưới nếu cần. Mỗi tài nguyên đều có một đường dẫn cơ sở thống nhất nằm dưới tiền tố `/api/v1`. Tài nguyên người dùng được expose tại `/api/v1/auth` và `/api/v1/user`; tài nguyên phục vụ phân tích xu hướng được nhóm dưới `/api/v1/radar`, `/api/v1/compare`, `/api/v1/graph`; tài nguyên hội thoại với chatbot được đặt tại `/api/v1/chat`; và các thao tác quản trị được nhóm dưới `/api/v1/admin`. Các định danh tài nguyên được truyền qua path parameter, ví dụ `/chat/session/:session_id/messages` mô tả tập tin nhắn của một phiên cụ thể; các điều kiện lọc và phân trang được truyền qua query parameter, ví dụ `?min_salary=15&location=Hanoi` cho luồng khám phá đồ thị.

Phương thức HTTP được lựa chọn đúng theo ngữ nghĩa của từng thao tác. `GET` được dùng cho mọi truy vấn an toàn và bất biến phía server như liệt kê dữ liệu radar, lấy chi tiết một session hay đọc thông tin người dùng hiện tại. `POST` được dùng cho mọi thao tác tạo mới tài nguyên hoặc khởi tạo một quá trình xử lý có hiệu ứng phụ, chẳng hạn đăng ký tài khoản, đăng nhập, làm mới token, tạo session mới hay gửi tin nhắn mới. `PUT` được dùng cho các thao tác cập nhật toàn bộ tài nguyên hiện hữu như cập nhật hồ sơ người dùng hay điều chỉnh một thiết lập cấu hình hệ thống. `DELETE` được dùng cho các thao tác xoá tài nguyên trong phạm vi quản trị.

Mã trạng thái HTTP được sử dụng tuân thủ chặt chẽ chuẩn của giao thức. Các phản hồi thành công sử dụng `200 OK` cho luồng đọc dữ liệu hoặc cập nhật, `201 Created` cho luồng tạo mới như đăng ký người dùng. Các phản hồi lỗi do client cung cấp dữ liệu không hợp lệ trả về `400 Bad Request`; lỗi liên quan đến xác thực dùng `401 Unauthorized`; lỗi liên quan đến phân quyền dùng `403 Forbidden`; trường hợp tài nguyên không tồn tại dùng `404 Not Found`; xung đột dữ liệu nghiệp vụ như đăng ký với email đã tồn tại dùng `409 Conflict`. Đối với lỗi phía server, `500 Internal Server Error` được trả về cho các lỗi không lường trước, `502 Bad Gateway` được trả về khi service AI ở phía sau trả về lỗi, và `503 Service Unavailable` được trả về khi cơ sở dữ liệu tạm thời không khả dụng.

### 4.2. Mô hình DTO

Mô hình Data Transfer Object được áp dụng nhất quán cho toàn bộ tầng giao tiếp giữa client và server. Lý do căn bản của việc tách DTO ra khỏi entity nghiệp vụ nằm ở chỗ hai loại đối tượng này tồn tại để phục vụ hai mục đích hoàn toàn khác nhau: entity phản ánh cấu trúc dữ liệu lưu trữ và các bất biến nghiệp vụ, còn DTO phản ánh hợp đồng giao tiếp giữa hệ thống và bên ngoài. Việc sử dụng trực tiếp entity làm payload sẽ dẫn đến nhiều vấn đề như rò rỉ các trường nhạy cảm ra ngoài, kết dính hợp đồng API với cấu trúc bảng cơ sở dữ liệu, và làm cho hai mặt phải tiến hoá đồng thời mỗi khi một bên thay đổi.

Một ví dụ minh hoạ rõ nét cho quan điểm này là entity `User` trong hệ thống. Entity này chứa trường `PasswordHash` đại diện cho mã băm mật khẩu được lưu trong PostgreSQL, được đánh dấu `json:"-"` để chắc chắn không bao giờ được tuần tự hoá ra ngoài. Tuy nhiên, để bảo đảm tính phòng vệ theo nhiều lớp, DTO phục vụ phản hồi của API như `MeResponse` chỉ khai báo đúng ba trường cần thiết cho client là `user_id`, `email` và `role`, hoàn toàn không tham chiếu đến trường mật khẩu hay các trường nội bộ khác. Như vậy, ngay cả khi tầng service vô tình trả về một entity đầy đủ, tầng DTO vẫn đóng vai trò như một bộ lọc cuối cùng quyết định những gì rời khỏi hệ thống.

Tương tự, các DTO phục vụ yêu cầu đầu vào được khai báo riêng cho từng endpoint. `RegisterRequest` chứa các trường `email`, `password`, `confirm_password` và `full_name`; `LoginRequest` chỉ chứa `email` và `password`; `RefreshTokenRequest` chỉ chứa `refresh_token`. Cách tách này cho phép từng endpoint chỉ chấp nhận đúng các trường liên quan, qua đó hạn chế hiện tượng mass assignment khi client cố tình gửi các trường không thuộc hợp đồng. Trong mã nguồn Go, toàn bộ DTO được đặt trong package `internal/dto` để tách biệt rõ ràng với package `internal/domain` dành cho entity nghiệp vụ.

### 4.3. Validation đầu vào

Validation đầu vào được tích hợp ngay tại tầng DTO thông qua cơ chế binding của Gin, vốn dựa trên thư viện `go-playground/validator`. Mỗi trường trong DTO yêu cầu được khai báo các ràng buộc trực tiếp qua struct tag, nhờ đó kiểm tra dữ liệu được thực hiện một cách khai báo, ngắn gọn và đặt cùng vị trí với khai báo cấu trúc. Cấu trúc `RegisterRequest` minh hoạ cách kết hợp nhiều quy tắc trong một khai báo duy nhất:

```go
type RegisterRequest struct {
    Email           string `json:"email" binding:"required,email"`
    Password        string `json:"password" binding:"required,min=8"`
    ConfirmPassword string `json:"confirm_password" binding:"required,eqfield=Password"`
    FullName        string `json:"full_name"`
}
```

Ràng buộc `required` bảo đảm trường tương ứng phải xuất hiện trong payload; ràng buộc `email` kiểm tra định dạng địa chỉ thư điện tử; ràng buộc `min=8` đặt yêu cầu độ dài tối thiểu cho mật khẩu; còn ràng buộc `eqfield=Password` kiểm tra trường `confirm_password` phải trùng khớp với trường `password` ngay trong cùng một payload, qua đó tránh việc người dùng nhập sai mật khẩu mà không phát hiện. Đối với các trường có ràng buộc theo nghiệp vụ như độ dài tối đa của một tin nhắn chat, ràng buộc `max=2000` được áp dụng nhằm ngăn ngừa các payload quá lớn có thể gây tốn tài nguyên cho cả Golang và service AI phía sau.

Quy trình xử lý tại tầng handler tuân theo một mẫu thống nhất: gọi `c.ShouldBindJSON` để vừa giải mã JSON vừa thực thi validation; nếu việc binding hoặc validation thất bại, handler trả về ngay mã `400 Bad Request` kèm thông điệp mô tả lỗi, không tiếp tục thực thi logic nghiệp vụ. Nhờ đó, tầng service chỉ nhận được những dữ liệu đã hợp lệ về mặt định dạng, qua đó đơn giản hoá đáng kể logic xử lý ở các lớp sâu hơn.

Ngoài validation cú pháp tại tầng DTO, các kiểm tra nghiệp vụ phức tạp hơn được đặt tại tầng service, ví dụ như kiểm tra email đã tồn tại trước khi đăng ký, kiểm tra trạng thái tài khoản có bị khoá hay không trước khi đăng nhập, hoặc kiểm tra quyền truy cập đối với một session chat cụ thể. Cách phân tầng này tuân thủ nguyên tắc tách biệt mối quan tâm, đồng thời cho phép từng loại lỗi nghiệp vụ được ánh xạ về một mã trạng thái HTTP phù hợp tại tầng handler.

### 4.4. Chuẩn hoá định dạng response

Để bảo đảm tính nhất quán cho phía frontend, hệ thống áp dụng một quy ước thống nhất về cấu trúc phản hồi. Các phản hồi mang dữ liệu danh sách hoặc dữ liệu phức hợp được bọc trong một envelope tối giản với trường `data`, ví dụ `Top4Response`, `RadarSearchResponse`, `CompareSearchResponse`, `GraphExploreResponse` và `ListUsersResponse` đều có duy nhất một trường `data` chứa nội dung tương ứng. Mẫu này cho phép bổ sung các trường metadata trong tương lai như phân trang hoặc tổng số bản ghi mà không phá vỡ hợp đồng hiện hữu.

Đối với các phản hồi mang dữ liệu xác thực, cấu trúc được mở rộng để chứa đồng thời nhiều trường ngữ nghĩa rõ ràng. Cụ thể, `AuthResponse` trả về kèm theo `access_token`, `refresh_token`, `token_type`, `expires_in` và một trường `message` tuỳ chọn, cho phép client xác định thời điểm token hết hạn để chủ động làm mới mà không phải giải mã token. Đối với các phản hồi thuần thông tin trạng thái, cấu trúc được rút gọn tối đa, ví dụ `StatusResponse` chỉ chứa các cờ boolean tương ứng với từng tính năng và chế độ bảo trì.

Đối với phản hồi lỗi, hệ thống sử dụng một DTO chung là `ErrorResponse` với một trường duy nhất là `message` mô tả nguyên nhân lỗi. Lựa chọn cấu trúc tối giản này dựa trên thực tế là mã trạng thái HTTP đã mang phần lớn ngữ nghĩa phân loại lỗi, trong khi `message` chỉ cần cung cấp thông tin bổ sung đủ để client hiển thị thông báo cho người dùng cuối hoặc ghi log phục vụ chẩn đoán. Ngữ cảnh chi tiết hơn của lỗi, nếu có, được ghi nhận trong log phía server thay vì trả ngược cho client, qua đó hạn chế việc rò rỉ chi tiết nội bộ ra bên ngoài.

### 4.5. Versioning API

Toàn bộ endpoint công khai được đặt dưới tiền tố `/api/v1`, qua đó áp dụng chiến lược versioning theo URL ngay từ giai đoạn đầu của dự án. Trong mã nguồn Go, việc gắn tiền tố này được thực hiện tập trung tại `router.go` thông qua việc tạo một nhóm `api := r.Group("/api/v1")` và mount toàn bộ route con vào nhóm này, nhờ đó mọi endpoint đều thừa hưởng đường dẫn cơ sở thống nhất mà không cần lặp lại tại từng handler.

Chiến lược versioning theo URL được lựa chọn vì ba lý do. Thứ nhất, phiên bản API hiện rõ trong địa chỉ, giúp người tích hợp xác định ngay phiên bản mình đang sử dụng mà không cần đọc header hay tài liệu kèm theo. Thứ hai, các công cụ phổ biến như Postman, trình duyệt, hệ thống cache trung gian và các pipeline kiểm thử đều hoạt động tự nhiên với URL khác nhau cho từng phiên bản. Thứ ba, khi xuất hiện thay đổi không tương thích ngược trong tương lai, việc tạo một nhóm `api/v2` song song với `api/v1` cho phép duy trì đồng thời cả hai phiên bản trong cùng một binary, qua đó các client cũ có thời gian chuyển đổi mà không bị gián đoạn dịch vụ. Các endpoint vận hành như `/health` và `/swagger` không gắn với phiên bản nghiệp vụ nên được đặt ở cấp gốc, tách khỏi nhóm `/api/v1`.

### 4.6. Tài liệu hoá API bằng Swagger

Tài liệu API được duy trì theo phương pháp documentation-as-code thông qua công cụ `swaggo/swag`. Mỗi handler được mô tả bằng một khối chú thích godoc đặt ngay phía trên định nghĩa hàm, sử dụng các thẻ đặc biệt mà công cụ có thể phân tích để sinh ra đặc tả OpenAPI. Mẫu chú thích điển hình bao gồm các thẻ `@Summary` tóm tắt mục đích, `@Tags` phân loại endpoint, `@Accept` và `@Produce` mô tả định dạng dữ liệu, `@Param` mô tả tham số đầu vào kèm theo DTO tương ứng, `@Success` mô tả phản hồi thành công, `@Failure` mô tả các trường hợp lỗi với mã trạng thái và DTO lỗi đi kèm, `@Router` xác định đường dẫn và phương thức HTTP, cùng với `@Security` cho biết endpoint yêu cầu xác thực Bearer Token.

Mỗi khi mã nguồn được build lại, lệnh sinh tài liệu tạo ra ba tệp `docs.go`, `swagger.json` và `swagger.yaml` trong thư mục `docs`, đồng thời Gin nhúng giao diện Swagger UI tại đường dẫn `/swagger/*any` thông qua `swaggo/gin-swagger`. Người tích hợp có thể truy cập trực tiếp giao diện này trên trình duyệt để đọc tài liệu, xem ví dụ payload, và thậm chí thực thi thử các yêu cầu HTTP ngay trên trình duyệt mà không cần đến công cụ ngoài.

Phương pháp này mang lại ba lợi ích đáng kể. Thứ nhất, tài liệu luôn được sinh trực tiếp từ mã nguồn và các struct DTO, do đó không thể tồn tại tình trạng tài liệu sai lệch so với hành vi thực tế của API sau mỗi lần thay đổi. Thứ hai, mọi nhà phát triển có thói quen đọc và viết godoc đều có thể đóng góp tài liệu mà không phải học cú pháp viết tài liệu tách rời. Thứ ba, đặc tả OpenAPI được sinh ra có thể tái sử dụng để tự động sinh client SDK hoặc tích hợp với các công cụ kiểm thử tự động, tạo nền tảng tốt cho việc mở rộng quy trình phát triển trong tương lai.

## 5. Bảo mật

### 5.1. Xác thực bằng JWT

Cơ chế xác thực của hệ thống được xây dựng quanh chuẩn JSON Web Token, một định dạng token có chữ ký số được sử dụng phổ biến cho các API trạng thái không. Việc lựa chọn JWT thay vì cookie phiên xuất phát từ đặc điểm phân tán của hệ thống microservices: token chứa đầy đủ thông tin cần thiết cho việc xác thực bên trong chính nó, do đó các service có thể xác thực yêu cầu mà không cần chia sẻ trạng thái phiên hay phụ thuộc vào một kho lưu trữ tập trung.

#### 5.1.1. Cấu trúc token

Mỗi token JWT trong hệ thống được cấu thành từ ba phần được phân tách bằng dấu chấm: header, payload và signature. Phần header khai báo thuật toán ký được sử dụng là HS256, tức HMAC kết hợp với hàm băm SHA-256. Phần payload chứa các claim cốt lõi phục vụ cho việc xác thực và phân quyền, bao gồm trường `sub` mang định danh người dùng, `email` chứa địa chỉ thư điện tử, `role` thể hiện vai trò hệ thống của người dùng, `token_type` phân biệt giữa access token và refresh token, `iat` ghi nhận thời điểm phát hành và `exp` xác định thời điểm hết hạn của token. Phần signature là kết quả ký HMAC-SHA256 lên hai phần đầu bằng khoá bí mật phía server, qua đó bảo đảm rằng mọi thay đổi trên header hoặc payload đều dẫn đến việc xác minh chữ ký thất bại tại server.

Khoá ký được nạp từ biến môi trường `JWT_SECRET` thông qua tầng cấu hình, không được hard-code trong mã nguồn. Việc giữ khoá ký bí mật và đủ dài là điều kiện tiên quyết cho tính an toàn của toàn bộ cơ chế xác thực, vì một khoá bị lộ sẽ cho phép kẻ tấn công tự tạo ra token hợp lệ với bất kỳ định danh nào.

#### 5.1.2. Access token và refresh token

Hệ thống áp dụng mô hình cặp token kép gồm access token và refresh token, mỗi loại đảm nhiệm một vai trò riêng và có vòng đời khác nhau. Access token có thời gian sống ngắn, được cấu hình ở mức 15 phút, và là loại token duy nhất được chấp nhận tại các endpoint nghiệp vụ. Refresh token có thời gian sống dài hơn nhiều, ở mức bảy ngày, và chỉ được chấp nhận tại endpoint `/auth/refresh` để đổi lấy một cặp token mới.

Cách phân tách này phục vụ hai mục đích đồng thời. Thứ nhất, thời gian sống ngắn của access token giới hạn cửa sổ tấn công trong trường hợp token bị rò rỉ, vì sau tối đa 15 phút token sẽ tự động mất hiệu lực và không thể tiếp tục bị sử dụng. Thứ hai, refresh token cho phép người dùng duy trì trạng thái đăng nhập trong thời gian dài mà không phải nhập lại mật khẩu sau mỗi vòng đời ngắn, đồng thời do refresh token chỉ được sử dụng tại một endpoint duy nhất nên bề mặt tiếp xúc với mạng cũng nhỏ hơn. Việc tạo cặp token được thực hiện tập trung tại hàm `buildTokenPair` của `AuthService`, sau đó được trả về cho client trong `AuthResponse` cùng với loại token Bearer và số giây còn lại trước khi access token hết hạn.

#### 5.1.3. Middleware xác thực

Việc thực thi xác thực được tập trung tại một bộ middleware chuyên trách trong package `internal/middleware`, qua đó loại bỏ hoàn toàn nhu cầu lặp lại logic xác thực ở từng handler. Hai middleware chính được cung cấp là `RequireAuth` cho các endpoint cần xác thực thông thường, và `RequireAdmin` cho các endpoint yêu cầu quyền quản trị.

Cả hai middleware đều tuân theo cùng một quy trình kiểm tra. Bước đầu tiên là kiểm tra sự hiện diện của header `Authorization` và xác nhận tiền tố `Bearer`. Bước thứ hai là gọi `ParseClaims` để giải mã JWT, trong đó hàm khởi tạo bắt buộc phải sử dụng thuật toán HMAC; mọi token sử dụng thuật toán ký khác đều bị từ chối ngay từ giai đoạn xác minh chữ ký, qua đó ngăn ngừa các tấn công nhằm hạ cấp thuật toán hoặc lợi dụng thuật toán `none`. Bước thứ ba là kiểm tra trường `token_type` để chắc chắn rằng chỉ access token mới được chấp nhận tại các endpoint nghiệp vụ, refresh token không thể được dùng nhầm chỗ. Nếu mọi bước đều thành công, middleware trích xuất `user_id`, `email` và `role` từ claim vào context của Gin để các handler phía sau có thể truy cập trực tiếp; ngược lại, middleware huỷ chuỗi xử lý và trả về `401 Unauthorized` kèm thông điệp mô tả tổng quát.

### 5.2. Băm mật khẩu

Mật khẩu của người dùng không bao giờ được lưu trữ ở dạng nguyên bản hoặc dạng băm thuần một chiều. Toàn bộ quá trình đăng ký và đăng nhập đều đi qua thư viện `golang.org/x/crypto/bcrypt`, thư viện chính thức hiện thực thuật toán bcrypt cho Go. Tại thời điểm đăng ký, hàm `bcrypt.GenerateFromPassword` được gọi để sinh ra một chuỗi băm có sẵn salt được nhúng bên trong; chuỗi này sau đó được lưu xuống PostgreSQL trong cột `password_hash` của bảng người dùng. Tại thời điểm đăng nhập, hàm `bcrypt.CompareHashAndPassword` được sử dụng để so khớp giữa mật khẩu được cung cấp và chuỗi băm đã lưu, không bao giờ phải khôi phục mật khẩu nguyên bản.

Thuật toán bcrypt được lựa chọn nhờ hai đặc điểm phù hợp với bài toán bảo vệ mật khẩu. Thứ nhất, thuật toán có salt ngẫu nhiên độc lập cho từng mật khẩu, qua đó vô hiệu hoá các tấn công sử dụng bảng băm dựng sẵn và bảo đảm rằng hai người dùng đặt cùng một mật khẩu vẫn cho ra hai chuỗi băm khác nhau trong cơ sở dữ liệu. Thứ hai, bcrypt được thiết kế là một thuật toán băm có chi phí tính toán điều chỉnh được thông qua tham số cost; chi phí này khiến cho ngay cả khi toàn bộ chuỗi băm bị rò rỉ, việc dò mật khẩu bằng vét cạn vẫn trở nên không khả thi trong thời gian hợp lý. Hệ thống sử dụng giá trị `bcrypt.DefaultCost` đang ở mức 10, đại diện cho khoảng 2^10 vòng nội bộ trên mỗi lần băm; giá trị này có thể được nâng lên trong tương lai khi tốc độ phần cứng cải thiện mà không phải thay đổi sơ đồ cơ sở dữ liệu, do thông tin về cost được nhúng sẵn trong chuỗi băm.

Đáng chú ý, thuộc tính `PasswordHash` của entity người dùng được khai báo với tag `json:"-"` để bảo đảm chuỗi băm không bao giờ bị tuần tự hoá ra phản hồi API, ngay cả khi tầng service vô tình trả về entity đầy đủ. Kết hợp với việc DTO `MeResponse` chỉ chứa các trường không nhạy cảm, hệ thống đạt được nhiều lớp phòng vệ độc lập trên cùng một dòng dữ liệu.

### 5.3. Phân quyền theo vai trò

Mô hình phân quyền của hệ thống ở giai đoạn hiện tại theo hướng đơn giản nhưng đủ chặt chẽ, dựa trên một trường `role` được lưu cùng thông tin người dùng và được nhúng vào trường `role` của claim JWT mỗi khi sinh token. Hai vai trò chính là `user` cho người dùng thông thường và `admin` cho người quản trị hệ thống.

Việc thực thi phân quyền được tập trung ngay tại tầng middleware. Đối với các endpoint nghiệp vụ thông thường yêu cầu xác thực, middleware `RequireAuth` chỉ kiểm tra tính hợp lệ của token mà không kiểm tra vai trò. Đối với toàn bộ nhóm route `/admin`, middleware `RequireAdmin` thực hiện thêm bước kiểm tra giá trị `role` trong claim phải đúng bằng `admin`, ngược lại sẽ trả về `403 Forbidden`. Cách bố trí này cho phép quyền quản trị được áp dụng cho cả một nhóm endpoint chỉ bằng một dòng khai báo tại router, đồng thời tránh nguy cơ bỏ sót kiểm tra quyền tại từng handler riêng lẻ.

Bên cạnh phân quyền theo vai trò, hệ thống còn áp dụng các kiểm soát ở cấp tài nguyên ngay tại tầng service. Ví dụ, khi người dùng truy cập tin nhắn của một session, service sẽ kiểm tra session đó có thực sự thuộc về `user_id` đang đăng nhập hay không, qua đó bảo đảm một người dùng không thể đọc lịch sử hội thoại của người khác ngay cả khi đoán đúng định danh session.

### 5.4. Bảo vệ các endpoint AI nội bộ

Các service AI viết bằng Python không được expose trực tiếp ra Internet và không nằm trong hợp đồng API công khai của hệ thống. Frontend không có hiểu biết về sự tồn tại của các service này và không thể gọi tới chúng. Mọi yêu cầu cần đến năng lực AI đều phải đi qua Golang API service, vốn là điểm vào duy nhất từ phía client.

Việc cách ly này được thực hiện ở hai tầng độc lập. Tầng thứ nhất là tầng mạng, nơi các service Python được đặt trong cùng mạng nội bộ với Golang API trong cấu hình Docker Compose; chỉ cổng của Golang được publish ra host hoặc ra reverse proxy, các cổng của service Python chỉ tồn tại bên trong mạng nội bộ Docker và không thể tiếp cận trực tiếp từ bên ngoài. Tầng thứ hai là tầng cấu hình, nơi địa chỉ của service AI được Golang đọc từ biến môi trường `PYTHON_AI_BASE_URL` trỏ tới tên service trong mạng nội bộ; cấu hình này không xuất hiện ở bất kỳ tệp công khai nào của frontend.

Cách phân lớp như vậy mang lại ba lợi ích bảo mật quan trọng. Thứ nhất, toàn bộ kiểm tra JWT và phân quyền được thực hiện tập trung tại Golang trước khi yêu cầu được chuyển tiếp sang phía AI, nhờ đó service AI không phải tự duy trì cơ chế xác thực riêng. Thứ hai, các giới hạn tốc độ và kiểm soát truy cập nếu được áp dụng trong tương lai cũng chỉ cần đặt tại Golang, không gây trùng lặp logic. Thứ ba, mọi cuộc gọi tới mô hình ngôn ngữ đều đi qua một điểm duy nhất, qua đó việc kiểm toán, ghi log và giới hạn chi phí trở nên khả thi.

### 5.5. CORS, kiểm soát đầu vào và giới hạn lưu lượng

Cross-Origin Resource Sharing được cấu hình tập trung tại router của Golang thông qua middleware `gin-contrib/cors`. Danh sách các origin được phép truy cập được nạp từ biến môi trường `ALLOWED_ORIGINS` thay vì dùng giá trị `*`, qua đó chỉ những domain frontend hợp lệ mới có thể gửi yêu cầu kèm credentials tới API. Các phương thức HTTP được phép giới hạn ở `GET`, `POST`, `PUT`, `PATCH`, `DELETE` và `OPTIONS`; các header được chấp nhận giới hạn ở `Origin`, `Content-Type`, `Authorization` và `X-Client-Type`; thời gian cache cho preflight được đặt ở mức 12 giờ nhằm giảm số lượng yêu cầu `OPTIONS` phải xử lý lại.

Đối với kiểm soát đầu vào, lớp phòng thủ đầu tiên đến từ chính cơ chế binding của Gin kết hợp với struct tag `binding` đã trình bày trong chương về thiết kế API. Mọi payload đều được kiểm tra cú pháp ngay tại tầng DTO trước khi đi vào logic nghiệp vụ. Lớp phòng thủ thứ hai đến từ việc sử dụng tham số hoá trong các truy vấn cơ sở dữ liệu thông qua `pgx`, qua đó loại bỏ hoàn toàn nguy cơ tấn công SQL injection vì giá trị do người dùng cung cấp không bao giờ được nối thẳng vào câu lệnh SQL. Đối với truy vấn Cypher trên Neo4j, cơ chế tham số hoá tương đương của driver chính thức được áp dụng nhất quán nhằm đạt được mức bảo vệ tương tự.

Về giới hạn lưu lượng, hệ thống ở giai đoạn hiện tại chưa áp dụng rate limiting cấp toàn cục, nhưng đã chuẩn bị sẵn các điểm gắn trong tầng middleware để bổ sung khi cần. Các endpoint nhạy cảm như `/auth/login` và đặc biệt là `/chat/session/:id/messages/stream` được xác định là các ứng viên ưu tiên cho việc áp dụng rate limit trong các phiên bản tiếp theo, vì chúng vừa có chi phí tính toán cao vừa là mục tiêu phổ biến của các cuộc tấn công vét cạn hoặc lạm dụng tài nguyên.

### 5.6. Quản lý thông tin nhạy cảm

Toàn bộ thông tin nhạy cảm của hệ thống được tách hoàn toàn khỏi mã nguồn và được quản lý thông qua biến môi trường. Tầng cấu hình của Golang sử dụng thư viện `godotenv` để nạp các giá trị từ tệp `.env` ở giai đoạn phát triển, trong khi ở môi trường vận hành các giá trị này được cung cấp trực tiếp từ hệ thống điều phối container hoặc từ kho bí mật của hạ tầng triển khai. Cấu hình tập trung trong struct `Config` quy định rõ danh sách các biến mà ứng dụng đọc, bao gồm `JWT_SECRET` cho khoá ký token, `PostgreSQL_CONNECTION_STRING` cho chuỗi kết nối cơ sở dữ liệu, nhóm `NEO4J_*` cho thông tin truy cập Neo4j, `PYTHON_AI_BASE_URL` cho điểm cuối của service AI, và `ALLOWED_ORIGINS` cho danh sách origin được phép.

Trong kho mã, chỉ tệp `.env.example` được commit nhằm minh hoạ tập biến mà ứng dụng kỳ vọng; tệp này chỉ nên chứa các giá trị mặc định không nhạy cảm hoặc các placeholder, không chứa khoá thật của môi trường vận hành. Tệp `.env` thực tế được liệt kê trong `.gitignore` để chắc chắn không bị đẩy lên kho mã, qua đó tránh hoàn toàn rủi ro lộ thông tin qua lịch sử git. Cách tổ chức này tuân thủ phương pháp luận twelve-factor về cấu hình ứng dụng, đồng thời cho phép cùng một artifact được triển khai ở nhiều môi trường khác nhau chỉ bằng việc thay đổi tập biến môi trường tương ứng.

Cuối cùng, các giá trị mặc định trong mã nguồn được đặt theo nguyên tắc fail-safe: nếu `PostgreSQL_CONNECTION_STRING` không được cung cấp, ứng dụng từ chối khởi động và trả về lỗi rõ ràng thay vì lặng lẽ chạy với một cấu hình không an toàn; nếu `JWT_SECRET` không được cung cấp, ứng dụng vẫn nhận diện được tình trạng cấu hình thiếu và cảnh báo, qua đó tránh tình huống production vô tình chạy với khoá ký mặc định công khai.

## 6. Tầng dữ liệu

Tầng dữ liệu của backend được tổ chức quanh hai hệ quản trị cơ sở dữ liệu chuyên biệt: PostgreSQL cho dữ liệu nghiệp vụ quan hệ và Neo4j cho dữ liệu có cấu trúc đồ thị. Mỗi loại cơ sở dữ liệu được lựa chọn dựa trên đặc trưng nội tại của dữ liệu mà nó lưu trữ, qua đó tận dụng tối đa các điểm mạnh riêng và tránh hiện tượng gò ép một mô hình lưu trữ duy nhất phải phục vụ mọi loại truy vấn.

### 6.1. Cơ sở dữ liệu nghiệp vụ PostgreSQL

PostgreSQL được sử dụng làm cơ sở dữ liệu nghiệp vụ chính, lưu trữ toàn bộ thông tin có ràng buộc giao dịch chặt chẽ như tài khoản người dùng, hồ sơ cá nhân, lịch sử hội thoại chatbot, các cờ cấu hình hệ thống và các bảng phục vụ thống kê analytics. Việc lựa chọn PostgreSQL xuất phát từ ba yếu tố: hỗ trợ giao dịch ACID đầy đủ, hệ kiểu dữ liệu phong phú bao gồm UUID, JSON và mảng, cùng với hệ sinh thái phần mở rộng đa dạng.

#### 6.1.1. Lược đồ cơ sở dữ liệu

Lược đồ được tổ chức quanh ba nhóm bảng chính. Nhóm thứ nhất gồm các bảng liên quan đến người dùng, trong đó bảng `users` là trung tâm với khoá chính kiểu UUID được sinh tự động bằng hàm `gen_random_uuid` thuộc phần mở rộng `pgcrypto`, kèm theo các trường `email`, `password_hash`, `full_name`, `subscription_tier`, `role` và `status`. Email được khai báo `UNIQUE NOT NULL` ở cấp cơ sở dữ liệu để chặn hoàn toàn các tài khoản trùng địa chỉ, đồng thời cho phép tận dụng chỉ mục duy nhất tự động cho mọi truy vấn tìm kiếm theo email. Bảng `user_profile` được tách riêng để chứa các thuộc tính hồ sơ có thể mở rộng như vai trò công việc, danh sách công nghệ, địa điểm và phần giới thiệu, qua đó giữ bảng `users` ở mức tinh gọn và ổn định.

Nhóm thứ hai gồm các bảng phục vụ chatbot. Bảng `chat_session` lưu các phiên hội thoại với khoá ngoại `user_id` tham chiếu tới `users(id)` kèm hành vi `ON DELETE CASCADE`, bảo đảm khi một tài khoản bị xoá thì toàn bộ session liên quan cũng bị dọn sạch một cách nhất quán. Bảng `chat_message` lưu từng tin nhắn trong session, có cột `role` được ràng buộc bằng `CHECK (role IN ('user', 'assistant', 'system'))` để chỉ chấp nhận đúng ba giá trị hợp lệ, cùng các trường `prompt_tokens`, `completion_tokens` và `finish_reason` phục vụ việc thống kê chi phí và phân tích chất lượng phản hồi. Toàn bộ các cột thời gian sử dụng kiểu `TIMESTAMPTZ` nhằm lưu trữ rõ ràng theo múi giờ, qua đó tránh các mơ hồ khi triển khai hệ thống ở nhiều địa lý khác nhau.

Nhóm thứ ba gồm các bảng phục vụ analytics và cấu hình. Bảng `page_visits` ghi nhận lượt truy cập theo cặp `(visit_date, ip_address)` với khoá chính kép, qua đó vừa khử trùng lặp tự nhiên trong ngày vừa cho phép truy vấn xu hướng theo ngày một cách nhanh chóng. Bảng `keyword_searches` lưu toàn bộ từ khoá tìm kiếm cùng endpoint phát sinh và thời điểm tìm kiếm, được khoá chính là `BIGSERIAL` tự tăng để phục vụ ghi log dữ liệu. Ngoài ra, các bảng cấu hình `settings` lưu các cờ vận hành như chế độ bảo trì và bật/tắt tính năng dưới dạng cặp khoá–giá trị, cho phép thay đổi hành vi hệ thống ngay tại thời điểm vận hành mà không cần triển khai lại.

#### 6.1.2. Quản lý migration

Toàn bộ thay đổi lược đồ được quản lý dưới dạng các tệp SQL được đánh số trong thư mục `migrations`. Hiện tại kho mã chứa năm tệp migration tương ứng với các giai đoạn tiến hoá của lược đồ: `0001_init.sql` khởi tạo ba bảng cốt lõi `users`, `chat_session` và `chat_message`; `0002_analytics.sql` bổ sung cột `role` cho bảng người dùng cùng hai bảng analytics; `0003_user_status.sql` mở rộng các trạng thái tài khoản; `0004_settings.sql` thêm bảng cấu hình; và `0005_feature_rag.sql` bổ sung cờ điều khiển tính năng RAG. Mỗi migration được viết theo nguyên tắc idempotent thông qua các mệnh đề `CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS` và `CREATE INDEX IF NOT EXISTS`, qua đó việc chạy lại migration trên một cơ sở dữ liệu đã được áp dụng một phần vẫn an toàn và không gây lỗi.

Cách đánh số tuần tự với tiền tố bốn chữ số bảo đảm thứ tự áp dụng được xác định rõ ràng và không gây nhầm lẫn khi nhiều thay đổi được phát triển song song. Mọi thay đổi lược đồ đều được đẩy vào kho mã dưới dạng tệp mới thay vì chỉnh sửa các tệp đã tồn tại, qua đó lịch sử tiến hoá của lược đồ được lưu giữ đầy đủ và có thể tái lập trên bất kỳ môi trường nào.

### 6.2. Cơ sở dữ liệu đồ thị Neo4j

Toàn bộ dữ liệu phản ánh quan hệ giữa các thực thể trong miền nghiệp vụ được lưu trữ trên Neo4j thay vì PostgreSQL. Mô hình dữ liệu sử dụng nhiều loại nút khác nhau bao gồm `Technology` mô tả các công nghệ, `Skill` mô tả các kỹ năng, `Company` mô tả các doanh nghiệp tuyển dụng và `Job` mô tả các tin tuyển dụng. Các mối liên kết giữa chúng được biểu diễn dưới dạng cạnh có nhãn, ví dụ `USES` thể hiện việc một công ty sử dụng một công nghệ. Lựa chọn này dựa trên đặc điểm bản chất của dữ liệu: các truy vấn phục vụ cho ba nhóm chức năng radar, compare và graph đều xoay quanh các thao tác đi theo nhiều bước trên đồ thị quan hệ, vốn là loại truy vấn mà mô hình quan hệ truyền thống xử lý kém hiệu quả trong khi Neo4j cùng ngôn ngữ Cypher lại tối ưu sẵn cho.

Repository tương ứng được tổ chức trong package `internal/repository/neo4jrepo` với ba file riêng biệt cho ba domain: `graph_repository.go`, `compare_repository.go` và `radar_repository.go`. Đáng chú ý là cách lập mô hình kết quả trả về dưới dạng các struct trung gian `RawNode`, `RawEdge` và `RawPath`, mỗi cấu trúc chứa định danh, nhãn và các thuộc tính ở dạng `map[string]interface{}`. Cách trừu tượng hoá này giữ cho tầng service không phụ thuộc trực tiếp vào kiểu của driver Neo4j, đồng thời cho phép tầng service tự quyết định việc chuẩn hoá tên thuộc tính, lọc các trường nội bộ và làm giàu dữ liệu trước khi trả về cho client.

Các nghiệp vụ tiêu biểu của handler `graph_handler.go` tương ứng với ba kiểu truy vấn trên Neo4j. Endpoint `/graph/explore` thực hiện hai bước: trước hết tìm các nút trung tâm theo danh sách từ khoá thông qua hàm `FindCenterNodes`, sau đó mở rộng vùng láng giềng theo độ sâu một hoặc hai cấp thông qua hàm `GetNeighborhood`. Endpoint `/graph/explore_by_location` truy vấn theo mẫu `Technology ← USES ← Company(location) → USES → OtherTechnology` để tìm các công nghệ thường được dùng chung tại một địa điểm cụ thể. Endpoint `/graph/road_analysis` sử dụng truy vấn shortest path không định hướng với giới hạn sáu bước, đồng thời ưu tiên các đường đi xuyên qua một nút `Company` khi tồn tại nhiều đường đi có cùng độ dài.

### 6.3. Truy vấn và tối ưu

Tối ưu truy vấn được tiếp cận đồng đều ở cả hai loại cơ sở dữ liệu, dựa trên ba nhóm kỹ thuật chính: lập chỉ mục, tham số hoá và xử lý sau truy vấn ở tầng ứng dụng.

Ở phía PostgreSQL, các chỉ mục được tạo có chủ đích trên các cột thường xuất hiện trong điều kiện lọc và sắp xếp. Trên bảng `keyword_searches`, hai chỉ mục `idx_keyword_searches_keyword` và `idx_keyword_searches_searched_at` lần lượt phục vụ các truy vấn nhóm theo từ khoá để tính top tìm kiếm và truy vấn theo khoảng thời gian để dựng các biểu đồ xu hướng. Trên bảng `users`, ràng buộc `UNIQUE` trên cột `email` đã tự động tạo ra chỉ mục duy nhất, qua đó việc tìm kiếm theo email trong luồng đăng nhập diễn ra ở độ phức tạp gần như hằng số. Trên bảng `page_visits`, khoá chính kép `(visit_date, ip_address)` vừa khử trùng lặp vừa cung cấp chỉ mục tự nhiên cho các truy vấn thống kê theo ngày.

Mọi truy vấn SQL trong tầng repository đều được viết với tham số hoá theo cú pháp `$1`, `$2` của `pgx`, tuyệt đối không sử dụng nối chuỗi với giá trị do người dùng cung cấp. Ngoài ích lợi rõ ràng về bảo mật, cách viết này còn cho phép PostgreSQL tái sử dụng plan thực thi cho cùng một câu truy vấn với các giá trị khác nhau, qua đó giảm chi phí lập kế hoạch truy vấn lặp lại. Đối với các trường hợp cần xử lý lỗi đặc thù, repository nhận diện mã lỗi gốc từ PostgreSQL, ví dụ mã `23505` cho vi phạm ràng buộc duy nhất được ánh xạ thành sentinel `ErrEmailTaken`, còn `pgx.ErrNoRows` được ánh xạ thành `ErrNotFound`. Cách ánh xạ này tách biệt rõ ràng giữa lỗi kỹ thuật và lỗi nghiệp vụ, cho phép tầng service và tầng handler đưa ra phản hồi phù hợp với từng tình huống.

Ở phía Neo4j, các truy vấn Cypher đều được tham số hoá thông qua tham số thứ hai của hàm `session.Run`, ví dụ `map[string]interface{}{"keywords": keywords}`. Cách viết này không chỉ ngăn ngừa nguy cơ Cypher injection mà còn cho phép Neo4j tận dụng cache câu truy vấn. Các session được khởi tạo với chế độ truy cập rõ ràng thông qua `AccessModeRead` hoặc `AccessModeWrite`, qua đó Neo4j có thể định tuyến truy vấn tới các replica phù hợp khi triển khai cluster trong tương lai.

Một số luồng có nhu cầu lọc theo các tiêu chí không nằm trực tiếp trên thuộc tính của nút, ví dụ lọc tin tuyển dụng theo mức lương tối thiểu hoặc theo vùng địa lý. Đối với mức lương, giá trị `min_salary` được tính từ trường hợp chuỗi tiếng Việt như "Từ X triệu" hoặc "X-Y triệu" thông qua hàm `parseSalaryMin` ở tầng service, sau đó được gắn lại vào nút như một thuộc tính tính toán trước khi trả về cho client. Đối với địa điểm, từ khoá người dùng nhập được mở rộng thành nhiều biến thể thông qua `ExpandLocationSearchTerms` để xử lý các trường hợp viết tắt và biến thể chính tả phổ biến, sau đó được dùng trong vế `WHERE` của truy vấn Cypher với toán tử `CONTAINS` kết hợp `toLower` để so khớp không phân biệt hoa thường. Cách kết hợp giữa truy vấn Cypher và xử lý hậu kỳ ở tầng service giúp giữ truy vấn cơ sở dữ liệu đơn giản trong khi vẫn cho phép logic nghiệp vụ phong phú.

### 6.4. Repository pattern

Repository pattern được áp dụng nhất quán cho cả hai loại cơ sở dữ liệu, đóng vai trò là ranh giới rõ ràng giữa logic truy vấn dữ liệu và logic nghiệp vụ. Mỗi repository được tổ chức quanh một nhóm bảng hoặc một nhóm thực thể đồ thị cụ thể: bên PostgreSQL có `UserRepository`, `UserProfileRepository`, `ChatSessionRepository`, `ChatMessageRepository`, `AnalyticsRepository`, `SettingsRepository`, cùng các repository chuyên biệt phục vụ ba domain phân tích là `RadarRepository`, `CompareRepository` và `GraphRepository`; bên Neo4j có ba repository tương ứng với ba domain đồ thị cùng tên. Việc đặt mỗi repository trong một tệp riêng giúp giữ kích thước mỗi tệp ở mức quản lý được và làm rõ phạm vi trách nhiệm.

Mỗi repository có một struct giữ tham chiếu tới connection pool hoặc driver tương ứng, kèm theo một hàm khởi tạo `New*Repository` để tiêm phụ thuộc từ bên ngoài. Toàn bộ phương thức của repository đều nhận `context.Context` như tham số đầu tiên, qua đó việc huỷ truy vấn được lan truyền tự nhiên khi client đóng kết nối hoặc khi vượt quá thời gian chờ. Kiểu dữ liệu trả về của các phương thức luôn là entity nghiệp vụ thuộc package `internal/domain` thay vì các struct nội bộ của driver, nhờ đó tầng service không bao giờ phải tiếp xúc với chi tiết kỹ thuật của tầng lưu trữ.

Lợi ích lớn nhất của mô hình này là khả năng cô lập sự thay đổi. Khi lược đồ cơ sở dữ liệu hoặc cấu trúc đồ thị thay đổi, các điều chỉnh chỉ giới hạn ở phạm vi của repository tương ứng; tầng service và tầng handler không cần biết đến các chi tiết đó. Ngoài ra, việc sử dụng các sentinel error như `ErrNotFound` và `ErrEmailTaken` cho phép tầng service phân biệt các kịch bản lỗi một cách bền vững mà không phải so khớp với chuỗi thông điệp lỗi, vốn dễ thay đổi và không ổn định.

Cuối cùng, một quy ước được tuân thủ xuyên suốt là repository chỉ chứa logic truy vấn dữ liệu, không chứa logic nghiệp vụ. Các thao tác như tính toán, lọc theo điều kiện phức hợp hoặc làm giàu dữ liệu đều được đặt tại tầng service, nơi có thể kết hợp đồng thời dữ liệu từ nhiều repository khác nhau cũng như từ các service AI. Cách phân định trách nhiệm này tuân thủ nguyên tắc separation of concerns, đồng thời tạo điều kiện thuận lợi cho việc kiểm thử đơn vị ở từng tầng một cách độc lập.

### 7. Đóng gói & triển khai với Docker

Toàn bộ hệ thống được đóng gói dưới dạng các container Docker và điều phối qua một file `docker-compose.yml` đặt ở thư mục gốc dự án. Cách tiếp cận này giúp các thành phần — vốn được viết bằng nhiều ngôn ngữ và phụ thuộc nhiều bộ thư viện khác nhau — chạy đồng nhất trên môi trường phát triển cục bộ và trên máy chủ triển khai, đồng thời tách biệt rõ giữa cấu hình ứng dụng (đi kèm image) và cấu hình môi trường (nạp từ `.env`).

### 7.1. Dockerfile cho từng service

Mỗi service trong hệ thống có một `Dockerfile` riêng, được thiết kế phù hợp với đặc thù ngôn ngữ và chuỗi công cụ tương ứng.

Đối với Go API, Dockerfile sử dụng kỹ thuật multi-stage build nhằm tách rời quá trình biên dịch và quá trình chạy. Ở giai đoạn đầu (stage `builder`), image gốc `golang:1.25-alpine` được dùng để tải các module qua `go mod download` rồi biên dịch toàn bộ source ở `cmd/api` thành một binary tĩnh duy nhất với cờ `CGO_ENABLED=0`. Việc tắt CGO bảo đảm binary không phụ thuộc thư viện C động và có thể chạy trên một base image rất nhỏ. Ở giai đoạn thứ hai, image `alpine:3.20` chỉ cài thêm `ca-certificates` để hỗ trợ các kết nối TLS ra ngoài (Neo4j AuraDB, OpenAI), sau đó copy binary `server` từ stage trước vào. Kết quả là image cuối cùng chỉ gồm một file thực thi tĩnh trên nền Alpine tối giản, dung lượng nhỏ và bề mặt tấn công hẹp; cổng 8080 được khai báo qua `EXPOSE`, lệnh khởi động đơn giản là `./server`.

Đối với service RAG (`src/ai-rag-core`), Dockerfile dựa trên `python-3.11-slim`. Do RAG cần biên dịch một số package phụ thuộc gốc C và phải kết nối PostgreSQL, image cài thêm `build-essential` và `libpq-dev` trước khi `pip install` các thư viện liệt kê trong `requirements.txt`. Một điểm đáng chú ý là quá trình build chủ động tải sẵn các mô hình `intfloat/multilingual-e5-base` và `BAAI/bge-reranker-v2-m3` ngay trong giai đoạn build thông qua một lệnh Python ngắn. Cách làm này giúp container khởi động nhanh hơn nhiều ở môi trường thật, vì trọng số mô hình đã nằm trong layer image thay vì phải tải lại mỗi lần thùng chứa được khởi tạo; bù lại, kích thước image sẽ lớn hơn và quá trình build cần dung lượng đĩa cùng băng thông đáng kể. Service được khởi động bằng `uvicorn app.main:app` lắng nghe trên cổng 8000.

Service `ml-clustering` không có `Dockerfile` riêng vì hiện tại hệ thống triển khai phần này dưới dạng tiến trình FastAPI cục bộ và một pipeline DVC sinh sẵn artefact; nếu sau này cần container hoá, có thể tái sử dụng khuôn mẫu của RAG nhưng lược bỏ phần tải mô hình embedding. Frontend cũng có Dockerfile riêng nhưng nằm ngoài phạm vi chương này.

### 7.2. docker-compose.yml

File `docker-compose.yml` ở thư mục gốc dự án khai báo toàn bộ thành phần phụ trợ và service ứng dụng cần thiết để chạy hệ thống. Các dịch vụ hạ tầng gồm `neo4j-local` (image `neo4j:5` kèm plugin APOC, cấu hình bộ nhớ heap 512MB–2GB, mở cổng 7474 cho HTTP và 7687 cho Bolt) và `redis` (image `redis:7-alpine`, cổng 6379). Cả hai đều có khối `volumes` ánh xạ thư mục dữ liệu nội bộ ra volume có tên (`neo4j_data`, `neo4j_logs`, `redis_data`) nhằm bảo toàn dữ liệu giữa các lần khởi động lại container.

Các service ứng dụng gồm `rag-service` (build từ `./src/ai-rag-core`, cổng 8000) và `golang-api` (build từ `./src/backend/golang-api`, cổng 8080). Ngoài ra hai phiên bản MLflow Tracking Server được khai báo song song — `mlflow` (v3.12) phục vụ RAG ở cổng 5001 và `mlflow-clustering` (v2.16.2) phục vụ pipeline phân cụm ở cổng 5002 — sử dụng backend SQLite cùng thư mục artefact gắn qua volume bind-mount.

Cấu hình mạng tận dụng mạng mặc định mà Docker Compose tự tạo cho stack: mỗi service truy cập service khác bằng đúng tên khai báo. Điều này thể hiện rõ ở biến môi trường `PYTHON_AI_BASE_URL` của `golang-api`, được override thành `http://rag-service:8000` ngay trong block `environment`; nhờ đó binary Go khi đóng gói trong container không cần biết địa chỉ IP của RAG mà chỉ cần phân giải tên service qua DNS nội bộ. Quan hệ phụ thuộc khởi động được thể hiện qua trường `depends_on`: `golang-api` chỉ được khởi động sau khi `rag-service` đã được Compose tạo. Riêng `neo4j-local` được trang bị `healthcheck` chạy lệnh `neo4j status` với chu kỳ 10 giây và 10 lần thử, vừa làm tín hiệu trực quan cho người vận hành, vừa làm cơ sở để các service phụ thuộc có thể chờ trạng thái khoẻ mạnh thay vì chỉ chờ tiến trình tồn tại. Tất cả service đều cấu hình `restart: unless-stopped` để tự khôi phục khi máy chủ khởi động lại hoặc khi tiến trình rơi ngoài ý muốn, trừ khi được dừng có chủ đích.

Một điểm cần lưu ý mang tính tổ chức: hai service MLflow hiện đang trỏ tới đường dẫn tuyệt đối thuộc máy của một thành viên (`/Users/koiita/...`) qua `volumes` và `--backend-store-uri`. Đây là di sản từ quá trình thiết lập ban đầu, cần được thay bằng đường dẫn tương đối hoặc volume có tên trước khi triển khai sang môi trường khác; phần này sẽ được nêu lại ở chương khó khăn và hướng giải quyết.

### 7.3. Cấu hình môi trường qua `.env`

Toàn bộ tham số nhạy cảm và khác biệt theo môi trường được tách ra khỏi mã nguồn và mô tả khuôn mẫu trong `.env.example` ở thư mục gốc dự án. File này chia thành các nhóm chức năng rõ ràng: Neo4j (cả AuraDB cloud và Neo4j cục bộ, kèm cờ `USE_LOCAL_NEO4J` để chuyển đổi), khoá API của các nhà cung cấp LLM (Gemini, OpenAI) cùng `LLM_PROVIDER` và `LLM_MODEL`, thông tin kết nối PostgreSQL, URL Redis, các biến tuỳ chọn cho LangSmith và biến `EMBED_SECRET` dùng để ký nội bộ trên đường gọi embedding. Khi triển khai, người vận hành sao chép `.env.example` thành `.env` và điền giá trị thực; Compose nạp file này cho cả `golang-api` và `rag-service` thông qua chỉ thị `env_file: .env`, sau đó cho phép từng service ghi đè các khoá cần thay đổi trong block `environment` của riêng nó.

Cách phân tách giữa dev và prod được thực hiện bằng cùng một bộ mã nguồn nhưng hai file `.env` khác nhau. Ở môi trường phát triển, hệ thống thường trỏ tới Neo4j cục bộ (`USE_LOCAL_NEO4J=true`, `NEO4J_LOCAL_URI=bolt://localhost:7687`), PostgreSQL chạy trên máy lập trình viên và OpenAI sử dụng khoá hạn ngạch nhỏ. Ở môi trường triển khai, cùng các biến đó sẽ trỏ tới Neo4j AuraDB qua kết nối `neo4j+s://`, cơ sở dữ liệu PostgreSQL chạy trên dịch vụ quản lý và Compose nạp khoá OpenAI sản xuất. Nhờ vậy không có thay đổi mã nguồn nào giữa hai môi trường — sự khác biệt được khoanh vùng hoàn toàn ở lớp cấu hình.

## 8. Kết luận chương

### 8.1. Tổng kết những kết quả đã đạt được

Chương này khép lại phần báo cáo về backend của dự án Data Mining, nơi nhóm đã xây dựng thành công một hệ thống đa thành phần đáp ứng đầy đủ các yêu cầu nghiệp vụ và kỹ thuật đặt ra từ đầu dự án. Nhìn lại toàn bộ quá trình thiết kế và triển khai, có thể tổng hợp các kết quả đã đạt được theo bốn nhóm chính: kiến trúc hệ thống, chất lượng API, bảo mật và vận hành.

Về kiến trúc hệ thống, backend đã được xây dựng theo mô hình microservices có ranh giới rõ ràng giữa các thành phần. Golang API service giữ vai trò là cổng vào duy nhất từ phía client, đảm nhiệm toàn bộ logic xác thực, điều phối và truy vấn dữ liệu nghiệp vụ. Các service AI viết bằng Python tại `ai-rag-core` và `ml-clustering` được tách hoàn toàn vào mạng nội bộ, mỗi service tập trung vào một loại workload chuyên biệt: pipeline RAG kết hợp truy xuất ngữ cảnh với sinh phản hồi bằng mô hình ngôn ngữ lớn, và pipeline phân cụm dữ liệu công nghệ dựa trên HDBSCAN với khả năng tra cứu trực tuyến. Cách phân lớp này cho phép ba loại workload có đặc tính tài nguyên rất khác nhau cùng tồn tại trong một hệ thống mà không ràng buộc lẫn nhau, đồng thời mở đường cho việc mở rộng từng thành phần một cách độc lập trong tương lai.

Về chất lượng API, hệ thống cung cấp một bộ endpoint phong phú bám sát các nguyên tắc REST, được nhóm thành sáu domain rõ rệt là `auth`, `radar`, `compare`, `graph`, `chat` và `admin`, toàn bộ nằm dưới tiền tố `/api/v1`. Mô hình DTO được áp dụng nhất quán nhằm tách hợp đồng giao tiếp khỏi entity nghiệp vụ, validation đầu vào được tích hợp khai báo ngay tại tầng DTO, và định dạng phản hồi tuân theo một quy ước thống nhất. Tài liệu API được sinh tự động bằng Swagger trực tiếp từ chú thích trong mã nguồn, qua đó loại bỏ rủi ro sai lệch giữa tài liệu và hành vi thực tế của hệ thống.

Về bảo mật, hệ thống triển khai một cơ chế xác thực hai lớp dựa trên cặp access token và refresh token theo chuẩn JWT, kết hợp với băm mật khẩu bcrypt và phân quyền theo vai trò ngay tại tầng middleware. Việc cô lập các service AI ở mạng nội bộ, kết hợp với cấu hình CORS có chọn lọc, tham số hoá toàn diện ở mọi truy vấn cơ sở dữ liệu và quản lý thông tin nhạy cảm qua biến môi trường, tạo nên nhiều lớp phòng vệ độc lập che chắn cho các điểm trọng yếu của hệ thống.

Về vận hành, toàn bộ hệ thống được đóng gói bằng Docker và mô tả qua Docker Compose, cho phép khởi chạy đầy đủ stack chỉ bằng một lệnh duy nhất. Lược đồ cơ sở dữ liệu PostgreSQL được quản lý qua các tệp migration đánh số tuần tự và idempotent, dữ liệu đồ thị trên Neo4j được truy cập qua các repository chuyên biệt, và mọi cấu hình môi trường đều được tách khỏi mã nguồn. Cách tổ chức này bảo đảm tính lặp lại của môi trường triển khai cũng như khả năng dịch chuyển hệ thống giữa nhiều nền tảng khác nhau mà không phải chỉnh sửa mã nguồn.

Nhìn ở góc độ học thuật, quá trình thực hiện phần backend đã giúp nhóm hệ thống hoá các kiến thức về thiết kế hệ thống phân tán, lập trình đồng thời trong Go, làm việc với cả cơ sở dữ liệu quan hệ và cơ sở dữ liệu đồ thị, cũng như áp dụng các thực hành bảo mật và vận hành hiện đại. Quan trọng hơn, các quyết định thiết kế được đưa ra trong dự án đều dựa trên đánh giá cân bằng giữa lợi ích kỹ thuật và chi phí triển khai ở giai đoạn hiện tại, thay vì chạy theo các xu hướng công nghệ mới mà chưa thực sự cần thiết.

### 8.2. Hướng phát triển tiếp theo

Bên cạnh các kết quả đã đạt được, một số hướng mở rộng đã được nhận diện trong quá trình phát triển và được dự kiến cho các giai đoạn tiếp theo của dự án. Những hướng mở rộng này được sắp xếp theo thứ tự ưu tiên dựa trên mức độ tác động đến trải nghiệm người dùng và độ chín của hạ tầng hiện tại.

Hướng đầu tiên là thay thế giao thức REST nội bộ giữa Golang và các service Python bằng gRPC. Ở quy mô hiện tại, REST kết hợp JSON đã đáp ứng tốt nhu cầu của hệ thống nhờ tính phổ dụng và dễ kiểm thử. Tuy nhiên, khi lưu lượng giao tiếp giữa các service tăng cao, đặc biệt là các luồng có nhiều lượt trao đổi nhỏ liên tiếp, gRPC sẽ mang lại ba lợi thế đáng kể. Thứ nhất, định dạng Protocol Buffers giúp giảm kích thước payload và tăng tốc độ tuần tự hoá so với JSON. Thứ hai, hợp đồng dữ liệu được định nghĩa tập trung trong các tệp `.proto`, có thể sinh ra mã client và server cho cả Go và Python một cách tự động, qua đó loại bỏ hoàn toàn nguy cơ lệch hợp đồng. Thứ ba, gRPC hỗ trợ streaming hai chiều một cách tự nhiên, vốn phù hợp hơn với các luồng chatbot phức tạp so với cơ chế SSE hiện tại.

Hướng thứ hai là bổ sung một hệ thống message queue như Kafka hoặc RabbitMQ cho các luồng không yêu cầu phản hồi đồng bộ. Hiện tại, mọi giao tiếp giữa các service đều theo mô hình request-response đồng bộ, mô hình này phù hợp với các luồng nghiệp vụ tương tác trực tiếp nhưng kém phù hợp với các tác vụ ngầm như ghi log analytics, cập nhật chỉ mục tìm kiếm hoặc kích hoạt lại pipeline phân cụm khi dữ liệu nguồn thay đổi. Việc đưa các tác vụ này sang một hàng đợi tin nhắn sẽ giảm tải cho Golang API, tăng độ chịu lỗi của hệ thống nhờ cơ chế retry tích hợp sẵn, và tạo điều kiện cho các luồng xử lý không đồng bộ phức tạp hơn trong tương lai.

Hướng thứ ba là tích hợp một lớp cache phân tán như Redis nhằm giảm tải cho cả PostgreSQL và Neo4j ở các luồng có tần suất truy vấn cao. Các ứng cử viên phù hợp cho việc cache bao gồm kết quả truy vấn radar và compare vốn tương đối ổn định trong khoảng thời gian ngắn, các bảng cấu hình `settings` được đọc trong hầu hết các yêu cầu, cũng như danh sách session chat của người dùng. Ngoài vai trò cache, Redis còn có thể đảm nhận thêm các chức năng phụ trợ như lưu danh sách token đã bị thu hồi để hỗ trợ logout chủ động, lưu trạng thái rate limit cho các endpoint nhạy cảm, và làm bộ điều phối phiên cho các luồng SSE khi hệ thống được nhân bản thành nhiều instance.

Hướng thứ tư là chuyển dịch toàn bộ hệ thống từ Docker Compose sang Kubernetes khi yêu cầu về tính sẵn sàng và mở rộng tự động trở nên cấp thiết. Docker Compose hiện nay đã đáp ứng tốt nhu cầu của môi trường phát triển và một môi trường vận hành quy mô nhỏ, tuy nhiên Kubernetes sẽ mang lại các khả năng mà Compose không có như tự động phục hồi container hỏng, mở rộng tự động dựa trên tải, cập nhật tuần tự không downtime, và quản lý bí mật ở cấp cluster. Cấu trúc cấu hình hiện tại của hệ thống đã sẵn sàng cho việc dịch chuyển này nhờ nguyên tắc tách cấu hình khỏi mã nguồn được tuân thủ ngay từ đầu, do đó chi phí chuyển đổi chủ yếu nằm ở việc viết các manifest Kubernetes và thiết lập hạ tầng cluster.

Hướng thứ năm là củng cố tầng quan sát hệ thống thông qua việc triển khai structured logging tập trung, hệ thống tracing phân tán với OpenTelemetry và các dashboard giám sát metrics với Prometheus và Grafana. Khi hệ thống được vận hành trong thực tế, khả năng quan sát chi tiết là điều kiện tiên quyết để chẩn đoán sự cố và tối ưu hiệu năng. Việc gắn trace ID xuyên suốt từ Golang sang các service Python sẽ cho phép tái dựng đầy đủ vòng đời của một yêu cầu khi xảy ra lỗi, qua đó rút ngắn đáng kể thời gian định vị nguyên nhân.

Ngoài năm hướng phát triển chính nêu trên, một số cải tiến nhỏ hơn cũng đã được nhận diện như áp dụng rate limiting cho các endpoint nhạy cảm, mở rộng hệ thống test tự động với độ phủ cao hơn, tích hợp pipeline CI/CD đầy đủ với các bước kiểm thử và quét bảo mật, cũng như nghiên cứu việc thay thế cơ chế phát hành token JWT hiện tại bằng các phương án có khả năng thu hồi token chủ động khi cần thiết.

Tóm lại, phần backend trong giai đoạn hiện tại đã đáp ứng được toàn bộ yêu cầu của đề tài và sẵn sàng phục vụ các kịch bản sử dụng thực tế. Các hướng phát triển tiếp theo không phải để khắc phục thiếu sót của thiết kế hiện tại, mà là để đưa hệ thống tiến lên một mức trưởng thành cao hơn về hiệu năng, độ tin cậy và khả năng vận hành ở quy mô lớn, đồng thời mở ra dư địa cho việc bổ sung các tính năng mới khi nhu cầu nghiệp vụ tiếp tục phát triển.

## 测试中发现的问题

- [ ] 点击预览图片时，左右移动会触发返回操作。
- [ ] 点击 confirm 之后，页面没有任何作业。
curl '<http://localhost:8000/api/batches/current>' \
  -H 'Accept: */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9,zh-TW;q=0.8,en;q=0.7' \
  -H 'Connection: keep-alive' \
  -b '__next_hmr_refresh_hash__=632a429ec8efa14754d1423bd35b11276f431a9f316c6df2; io=P_19-GGdxV28GcMOAAAA' \
  -H 'Referer: <http://localhost:8000/>' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"'

Response:
{
    "id": 1,
    "child_id": 1,
    "name": "1月2日作业",
    "status": "active",
    "deadline_at": "2026-01-04T15:59:00",
    "completed_at": null,
    "created_at": "2026-01-02T04:45:25",
    "updated_at": "2026-01-02T04:47:25",
    "items": [
        {
            "id": 1,
            "batch_id": 1,
            "source_image_id": null,
            "subject": {
                "id": 2,
                "name": "语文",
                "color": "#EF4444",
                "sort_order": 2
            },
            "text": "完成培优卷两张。期末综合过关练习(一)(二)。",
            "key_concept": null,
            "status": "todo",
            "started_at": null,
            "finished_at": null,
            "created_at": "2026-01-02T04:47:25"
        },
        {
            "id": 2,
            "batch_id": 1,
            "source_image_id": null,
            "subject": {
                "id": 1,
                "name": "数学",
                "color": "#3B82F6",
                "sort_order": 1
            },
            "text": "期末综合素养(基础卷)",
            "key_concept": null,
            "status": "todo",
            "started_at": null,
            "finished_at": null,
            "created_at": "2026-01-02T04:47:25"
        },
        {
            "id": 3,
            "batch_id": 1,
            "source_image_id": null,
            "subject": {
                "id": 1,
                "name": "数学",
                "color": "#3B82F6",
                "sort_order": 1
            },
            "text": "复习课本，完成P106-110。",
            "key_concept": null,
            "status": "todo",
            "started_at": null,
            "finished_at": null,
            "created_at": "2026-01-02T04:47:25"
        }
    ],
    "images": [],
    "vlm_parse_result": null
}

## 功能模块

- 需要增加一个简单的上传作业的实现，从微信直接上传图创建作业。

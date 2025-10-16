import unittest
import requests
import time
from api_doc import ElasticsearchApiDoc


class TestElasticsearchApi(unittest.TestCase):
    def setUp(self):
        """测试前的准备工作"""
        self.base_url = "http://localhost:9200"
        self.test_index = "test_index_" + str(int(time.time()))
        self.test_type = "test_doc"
        self.doc_ids = []
        self.api_doc = ElasticsearchApiDoc()
        
    def tearDown(self):
        """测试后的清理工作"""
        # 删除测试过程中创建的索引
        try:
            requests.delete(f"{self.base_url}/{self.test_index}")
        except:
            pass
    
    def test_create_index(self):
        """测试创建索引 API"""
        index_settings = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                self.test_type: {
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"}
                    }
                }
            }
        }
        response = requests.put(
            f"{self.base_url}/{self.test_index}", 
            json=index_settings
        )
        
        self.assertEqual(response.status_code, 200, f"创建索引失败: {response.text}")
        data = response.json()
        self.assertTrue(data["acknowledged"], "索引创建未被确认")
        
    def test_create_document(self):
        """测试创建文档 API"""
        # 先确保索引存在
        self.test_create_index()
        
        # 创建文档
        doc_data = {
            "name": "test_document"
        }
        
        response = requests.post(
            f"{self.base_url}/{self.test_index}/{self.test_type}/", 
            json=doc_data
        )
        
        self.assertEqual(response.status_code, 201, f"创建文档失败: {response.text}")
        data = response.json()
        self.assertTrue(data["created"], "文档创建未被确认")
        self.assertIn("_id", data, "响应中缺少文档ID")
        
        # 保存文档ID供后续测试使用
        self.doc_ids.append(data["_id"])
        
    def test_get_document(self):
        """测试获取文档 API"""
        # 先创建一个文档
        self.test_create_document()
        doc_id = self.doc_ids[0]
        
        # 获取文档
        response = requests.get(
            f"{self.base_url}/{self.test_index}/{self.test_type}/{doc_id}"
        )
        
        self.assertEqual(response.status_code, 200, f"获取文档失败: {response.text}")
        data = response.json()
        self.assertTrue(data["found"], "文档未找到")
        self.assertEqual(data["_id"], doc_id, "返回的文档ID不匹配")
        self.assertEqual(data["_source"]["name"], "test_document", "文档内容不匹配")
        
    def test_delete_document(self):
        """测试删除文档 API"""
        # 先创建一个文档
        self.test_create_document()
        doc_id = self.doc_ids[0]
        
        # 删除文档
        response = requests.delete(
            f"{self.base_url}/{self.test_index}/{self.test_type}/{doc_id}"
        )
        
        self.assertEqual(response.status_code, 200, f"删除文档失败: {response.text}")
        data = response.json()
        self.assertTrue(data["found"], "文档未找到")
        
        # 验证文档已被删除
        verify_response = requests.get(
            f"{self.base_url}/{self.test_index}/{self.test_type}/{doc_id}"
        )
        
        verify_data = verify_response.json()
        self.assertFalse(verify_data.get("found", False), "文档应该已被删除")
        
    def test_api_integrity(self):
        """测试 API 文档的完整性"""
        # 验证 API 文档中的节点数量
        nodes = self.api_doc.get_nodes()
        self.assertEqual(len(nodes), 4, "API文档中的节点数量不正确")
        
        # 验证必要的 API 是否都包含在内
        api_paths = [node.path for node in nodes]
        expected_paths = [
            "/${p_index}/${p_type}/",
            "/${p_index}/${p_type}/${p_id}",
            "/${p_index}/${p_type}/${p_id}",
            "/${p_index}"
        ]
        
        for path in expected_paths:
            self.assertIn(path, api_paths, f"API路径 {path} 未包含在API文档中")


if __name__ == '__main__':
    unittest.main()
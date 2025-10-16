import pickle
from typing import Dict, Set

import msgspec
from api.api_node import ApiNode
from basic.http.content_type import ContentType
from basic.http.http_request import HTTPMethod
from interface.docable import Docable
from typing_extensions import override


class ApiDoc(Docable):
    apinode_list = [
        ApiNode(path='/dede/login.php',
                method=HTTPMethod.GET,
                ),
        ApiNode(path='/dede/login.php',
                method=HTTPMethod.POST,
                # headers='{"Content-Type":"application/x-www-form-urlencoded"}',
                # params='gotopage=${q_gotopage}',
                headers='{"Content-Type":"multipart/form-data"}',
                data = '{"gotopage": "${dv_gotopage}","dopost":"${dv_dopost}","adminstyle":"${dv_adminstyle}","userid":"${dv_userid}","pwd":"${dv_pwd}","validate":"${dv_validate}","sm1":"${dv_sm1}"}'
                ),
        ApiNode(
            path="/dede/tpl.php",
            method=HTTPMethod.GET,
            params="action=${q_action}&token=&filename=${q_filename}&content=${q_content}",
        ),
        ApiNode(
            path="/dede/content_list.php",
            method=HTTPMethod.GET,
            params="dopost=${q_dopost}&cid=${q_cid}&keyword=${q_keyword}&orderby=${q_orderby}&flag=&imageField.x=${q_imageField.x}&imageField.y=${q_imageField.y}",
        ),
        ApiNode(
            path="/dede/feedback_main.php",
            method=HTTPMethod.GET,
        ),
        ApiNode(
            path="/dede/index_menu_load.php",
            method=HTTPMethod.GET,
            params="openitem=${q_openitem}",
        ),
        ApiNode(
            path="/dede/action_search.php",
            method=HTTPMethod.POST,
            # headers='{"Content-Type":"application/x-www-form-urlencoded"}',
            headers='{"Content-Type":"multipart/form-data"}',
            data='{"keyword":"${dv_keyword}"}',
        ),
        ApiNode(
            path="/dede/article_description_main.php",
            method=HTTPMethod.POST,
            # headers='{"Content-Type":"application/x-www-form-urlencoded"}',
            headers='{"Content-Type":"multipart/form-data"}',
            data='{"channel":"${dv_channel}", "dsize":"${dv_dsize}", "table":"${dv_table}", "field":"${dv_field}", "msize":"${dv_msize}", "pagesize":"${dv_pagesize}", "sid":"${dv_sid}", "eid":"${dv_eid}", "dojob":"${dv_dojob}", "Submit":"${dv_Submit}"}',
        ),

        ApiNode(
            path="/dede/co_getsource_url_action.php",
            method=HTTPMethod.GET,
            params="nid=${q_nid}&totalnum=${q_totalnum}&startdd=${q_startdd}&pagesize=${q_pagesize}&sptime=${q_sptime}&islisten=${q_islisten}",
        ),
        ApiNode(
            path="/dede/stepselect_main.php",
            method=HTTPMethod.GET,
            params="egroup=${q_egroup}",
        ),
        ApiNode(
            path="/dede/file_manage_main.php",
            method=HTTPMethod.GET,
            params="activepath=${q_activepath}",
        ),
        ApiNode(
            path="/dede/media_main.php",
            method=HTTPMethod.GET,
            params="dopost=${q_dopost}",
        ),
        ApiNode(
            path="/dede/co_export.php",
            method=HTTPMethod.GET,
            params="nid=${q_nid}&totalcc=${q_totalcc}&channelid=${q_channelid}&dopost=${q_dopost}&typeid=${q_typeid}&autotype=${q_autotype}&arcrank=${q_arcrank}&pagesize=${q_pagesize}&randcc=${q_randcc}&imageField.x=${q_imageFieldv_x}&imageField.y=${q_imageFieldv_y}",
        ),
        ApiNode(
            path="/dede/makehtml_all.php",
            method=HTTPMethod.POST,
            # headers='{"Content-Type":"application/x-www-form-urlencoded"}',
            headers='{"Content-Type":"multipart/form-data"}',
            data='{"action":"${dv_action}", "uptype":"${dv_uptype}", "starttime":"${dv_starttime}", "startid":"${dv_startid}", "Submit":"${dv_Submit}"}',
        ),
        ApiNode(
            path="/dede/baidunews.php",
            method=HTTPMethod.POST,
            params="do=${q_do}",
            # headers='{"Content-Type":"application/x-www-form-urlencoded"}',
            headers='{"Content-Type":"multipart/form-data"}',
            data='{"filename":"${dv_filename}", "button":"${dv_button}"}',
        ),
        ApiNode(
            path="/dede/plus_edit.php",
            method=HTTPMethod.GET,
            params="dopost=${q_dopost}&aid=${q_aid}",
        ),
        ApiNode(
            path="/dede/index_body.php",
            method=HTTPMethod.GET,
            params="dopost=${q_dopost}",
        ),
        ApiNode(
            path="/dede/plus_edit.php",
            method=HTTPMethod.GET,
            params="dopost=${q_dopost}&aid=${q_aid}",
        )

    ]

    nodes: Set[ApiNode] = set(apinode_list)
    api_doc: Dict[bytes, ApiNode] = {
        # msgspec.msgpack.encode(node): node for node in nodes
        node: node for node in nodes
    }

    @override
    def get_nodes(self):
        return self.nodes

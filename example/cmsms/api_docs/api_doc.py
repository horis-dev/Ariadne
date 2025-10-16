from typing import Dict, Set

import msgspec
from api.api_node import ApiNode
from basic.http.content_type import ContentType
from basic.http.http_request import HTTPMethod
from interface.docable import Docable
from typing_extensions import override

class CmsmsApiDoc(Docable):
    a0 = ApiNode(
        path = "/index.php",
        method = HTTPMethod.GET,
    )

    a1 = ApiNode(
        path = "/admin/login.php",
        method = HTTPMethod.GET,
    )

    a2 = ApiNode(
        path = "/admin/login.php",
        method = HTTPMethod.POST,
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"username":"${dv_username}","password":"${dv_password}","loginsubmit":"Submit"}'
    )

    a3 = ApiNode(
        path="/admin/index.php",
        method=HTTPMethod.GET,
        params="__c=${q___c}",
    )

    a4 = ApiNode(
        path="/admin/moduleinterface.php",
        method=HTTPMethod.POST,
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"mact":"DesignManager,m1_,admin_edit_template,0","__c":"${dv___c}","m1_tpl":"${dv_m1_tpl}","m1_submit":"Submit","m1_name":"${dv_m1_name}","m1_contents":"${dv_m1_contents}"}',
        filter_id="admin_edit_template",
    )

    a5 = ApiNode(
        path="/admin/moduleinterface.php",
        method=HTTPMethod.POST,
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"mact":"DesignManager,m1_,admin_settings,0","__c":"${dv___c}","m1_submit":"${dv_m1_submit}","m1_lock_timeout":"${dv_m1_lock_timeout}","m1_lock_refresh":"${dv_m1_lock_refresh}"}',
        filter_id="admin_settings",
    )


    a6 = ApiNode(
        path="/admin/moduleinterface.php",
        method=HTTPMethod.POST,
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"mact":"ModuleManager,m1_,setprefs,0","__c":"${dv___c}","m1_reseturl":"${dv_m1_reseturl}","m1_dl_chunksize":"${dv_m1_dl_chunksize}","m1_latestdepends":"${dv_m1_latestdepends}"}',
        filter_id="setprefs",
    )
    

    a7 = ApiNode(
        path="/admin/moduleinterface.php",
        method=HTTPMethod.POST,
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"mact":"CMSContentManager,m1_,admin_general_tab,0","__c":"${dv___c}","m1_submit":"Submit","m1_locktimeout":"${dv_m1_locktimeout}","m1_lockrefresh":"${dv_m1_lockrefresh}","m1_template_list_mode":"alldesign" }',
        filter_id="admin_general_tab",
    ) # __c  60 120


    a8 = ApiNode(
        path="/admin/moduleinterface.php",
        method=HTTPMethod.POST,
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"mact":"News,m1_,addcategory,0","__c":"${dv___c}","m1_name":"${dv_m1_name}","m1_parent":"-1","m1_submit":"Submit"}',
        filter_id="addcategory",
    ) # __c  name 


    a9 = ApiNode(
        path="/admin/listbookmarks.php",
        method=HTTPMethod.GET,
        params="__c=${q___c}",
    )


    a10 = ApiNode(
        path="/admin/addbookmark.php",
        method=HTTPMethod.POST,
        params="__c=${q___c}",
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"__c":"${dv___c}","title":"${dv_title}","url":"${dv_url}","addbookmark":"${dv_addbookmark}"}',
    )


    a11 = ApiNode(
        path="/admin/listusertags.php",
        method=HTTPMethod.GET,
        params="__c=${q___c}",
    )


    a12 = ApiNode(
        path="/admin/siteprefs.php",
        method=HTTPMethod.POST,
        params="__c=${q___c}",
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"__c":"${dv___c}","active_tab":"smarty","editsiteprefs":"true","submit":"Submit","use_smartycache":"${dv_use_smartycache}","use_smartycompilecheck":"${dv_use_smartycompilecheck}"}',
    )# __c __c 0 1


    a13 = ApiNode(
        path="/admin/systemmaintenance.php",
        method=HTTPMethod.POST,
        params="__c=${q___c}",
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"clearcache":"Clear"}',
        filter_id="clearcache",
    ) # __c


    a14 = ApiNode(
        path="/admin/systemmaintenance.php",
        method=HTTPMethod.POST,
        params="__c=${q___c}",
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"updatehierarchy":"Update"}',
        filter_id="updatehierarchy",
    ) # __c


    a15 = ApiNode(
        path="/admin/systemmaintenance.php",
        method=HTTPMethod.POST,
        params="__c=${q___c}",
        headers=f'{{"Content-Type":"{ContentType.MULTIPART_FORM_DATA.value}"}}',
        data='{"updateurls":"Update"}',
        filter_id="updateurls",
    ) # __c

    a16 = ApiNode(
        path="/admin/moduleinterface.php",
        method=HTTPMethod.GET,
        params="mact=DesignManager,m1_,admin_settings,0&__c=${q___c}",
        filter_id="DesignManager",
    ) # __c

    a17 = ApiNode(
        path="/admin/moduleinterface.php",
        method=HTTPMethod.GET,
        params="mact=CMSContentManager,m1_,admin_settings,0&__c=${q___c}",
        filter_id="CMSContentManager",
    ) # __c

    a18 = ApiNode(
        path="/admin/moduleinterface.php",
        method=HTTPMethod.GET,
        params="mact=News,m1_,admin_settings,0&__c=${q___c}",
        filter_id="News",
    ) # __c

    a19 = ApiNode(
        path="/admin/moduleinterface.php",
        method=HTTPMethod.GET,
        params="mact=FileManager,m1_,admin_settings,0&__c=${q___c}",
        filter_id="FileManager",
    ) # __c

    a20 = ApiNode(
        path="/admin/moduleinterface.php",
        method=HTTPMethod.GET,
        params="mact=ModuleManager,m1_,defaultadmin,0&__c=${q___c}",
        filter_id="ModuleManager",
    ) # __c


    nodes: Set[ApiNode] = {
        a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18, a19, a20
    }

    node_list: list[ApiNode] = [
        a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18, a19, a20
    ]

    api_doc: Dict[bytes, ApiNode] = {
        msgspec.msgpack.encode(node): node for node in nodes
    }

    @override
    def get_nodes(self):
        return self.nodes

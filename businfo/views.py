from django.shortcuts import render
import requests
import json
from django.conf import settings
from datetime import datetime
import logging
from django.http import JsonResponse
import os
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


def get_access_token():
    """獲取 TDX API 的存取令牌
    使用 OAuth2 認證機制，透過 client credentials 方式獲取存取令牌
    回傳值：access_token 字串
    """
    url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": settings.TDX_APP_ID,
        "client_secret": settings.TDX_APP_KEY
    }
    
    # 添加除錯訊息
    print(f"使用的 App ID: {settings.TDX_APP_ID}")
    print(f"使用的 App Key: {settings.TDX_APP_KEY}")
    
    response = requests.post(url, headers=headers, data=data)
    resp_json = response.json()
    
    if response.status_code != 200:
        print(f"API 回應狀態碼: {response.status_code}")
        print(f"API 回應內容: {resp_json}")
        raise Exception(f"TDX 認證失敗: {resp_json}")
    
    return resp_json["access_token"]

def get_bus_data(route_name):
    """獲取公車即時資訊，並回傳起點與終點站名
    參數：
        route_name: 公車路線名稱
    回傳值：
        result: 公車即時資訊列表
        start_stop: 起點站名
        end_stop: 終點站名
    """
    access_token = get_access_token()
    url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/Taichung?$filter=RouteName/Zh_tw eq '{route_name}'&$format=JSON"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"獲取公車資訊失敗: {response.text}")
    
    data = response.json()
    result = []
    
    for bus in data:
        # 獲取站牌名稱
        stop_name = bus.get('StopName', {}).get('Zh_tw', '未知站牌')
        # 獲取方向（0: 去程, 1: 返程）
        direction = bus.get('Direction', 0)
        # 獲取車牌號碼
        plate_number = bus.get('PlateNumb', '未知車牌')
        # 獲取預估到站時間（秒）
        estimate_time = bus.get('EstimateTime')
        # 獲取站牌順序
        stop_sequence = bus.get('StopSequence', 0)
        
        # 處理預估到站時間顯示格式
        if estimate_time is None:
            time_str = "未發車"
        elif estimate_time == 0:
            time_str = "即將到站"
        else:
            time_str = f"{estimate_time} 秒"
        
        result.append({
            'stop_name': stop_name,
            'direction': direction,
            'plate_number': plate_number,
            'estimate_time': time_str,
            'stop_sequence': stop_sequence
        })
    
    # 根據方向和站牌順序排序，確保顯示順序正確
    result.sort(key=lambda x: (x['direction'], x['stop_sequence']))
    
    # 取得起點與終點站名（只取去程方向）
    start_stop = end_stop = ''
    if result:
        # 只取 direction=0 的站牌序列
        dir0_stops = [r for r in result if r['direction'] == 0]
        if dir0_stops:
            start_stop = dir0_stops[0]['stop_name']
            end_stop = dir0_stops[-1]['stop_name']
    
    return result, start_stop, end_stop

def get_stop_info(token, stop_name):
    """搜尋台中市站牌資訊
    參數：
        token: TDX API 存取令牌
        stop_name: 站牌名稱（支援模糊搜尋）
    回傳值：
        站牌資訊列表
    """
    try:
        headers = {"Authorization": f"Bearer {token}"}
        # 使用 contains 進行模糊搜尋
        stop_url = (
            "https://tdx.transportdata.tw/api/basic/v2/Bus/StopOfRoute/City/Taichung"
            f"?$filter=contains(StopName/Zh_tw,'{stop_name}')"
            "&$format=JSON"
        )
        response = requests.get(stop_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"搜尋站牌失敗: {str(e)}")
        raise

def get_estimated_time(token, route_name, stop_name):
    """獲取台中市預估到站時間
    參數：
        token: TDX API 存取令牌
        route_name: 公車路線名稱
        stop_name: 站牌名稱
    回傳值：
        預估到站時間資訊列表
    """
    try:
        headers = {"Authorization": f"Bearer {token}"}
        # 使用 contains 進行模糊搜尋
        estimate_url = (
            "https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/Taichung"
            f"?$filter=contains(RouteName/Zh_tw,'{route_name}') and contains(StopName/Zh_tw,'{stop_name}')"
            "&$format=JSON"
        )
        response = requests.get(estimate_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"獲取預估到站時間失敗: {str(e)}")
        raise

def get_route_info(token, route_name):
    """獲取台中市路線資訊
    參數：
        token: TDX API 存取令牌
        route_name: 公車路線名稱
    回傳值：
        路線詳細資訊
    """
    try:
        headers = {"Authorization": f"Bearer {token}"}
        # 使用 contains 進行模糊搜尋
        route_url = (
            "https://tdx.transportdata.tw/api/basic/v2/Bus/Route/City/Taichung"
            f"?$filter=contains(RouteName/Zh_tw,'{route_name}')"
            "&$format=JSON"
        )
        response = requests.get(route_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"獲取路線資訊失敗: {str(e)}")
        raise

def bus_search(request):
    """處理公車查詢請求
    主要功能：
    1. 接收使用者查詢參數
    2. 獲取站牌和路線資訊
    3. 整合預估到站時間
    4. 回傳查詢結果
    """
    context = {
        'stop_name': '',
        'direction': '',
        'arrival_times': [],
        'error': None
    }
    
    if request.method == 'POST':
        stop_name = request.POST.get('stop_name', '').strip()
        direction = request.POST.get('direction')
        
        if not stop_name or direction is None:
            context['error'] = '請輸入站牌名稱並選擇方向'
            return render(request, 'bus_search.html', context)
        
        try:
            # 獲取 TDX token
            token = get_access_token()
            
            # 搜尋站牌和路線
            stops_data = get_stop_info(token, stop_name)
            
            if not stops_data:
                context['error'] = f'找不到站牌：{stop_name}'
                return render(request, 'bus_search.html', context)
            
            arrival_times = []
            processed_routes = set()  # 用於追踪已處理的路線，避免重複
            
            # 整理站牌和路線資訊
            for stop_route in stops_data:
                route_name = stop_route.get('RouteName', {}).get('Zh_tw', '')
                stop_name = stop_route.get('StopName', {}).get('Zh_tw', '')
                
                # 獲取預估到站時間
                estimates = get_estimated_time(token, route_name, stop_name)
                
                for estimate in estimates:
                    est_direction = str(estimate.get('Direction'))
                    
                    # 只處理符合搜尋方向的路線，且每個路線只處理一次
                    route_key = f"{route_name}_{est_direction}"
                    if est_direction == direction and route_key not in processed_routes:
                        processed_routes.add(route_key)
                        
                        # 計算預估時間（分鐘）
                        est_time = estimate.get('EstimateTime', 0)
                        if est_time is not None:
                            est_time = est_time // 60
                        else:
                            est_time = -1
                        
                        # 獲取路線詳細資訊
                        route_info = get_route_info(token, route_name)
                        route_description = ''
                        if route_info:
                            route_description = route_info[0].get('RouteName', {}).get('Zh_tw', '')
                            
                        arrival_info = {
                            'route_name': route_name,
                            'route_description': route_description,
                            'stop_name': stop_name,
                            'estimated_time': est_time,
                            'plate_numb': estimate.get('PlateNumb', ''),
                            'direction': '去程' if direction == '0' else '返程',
                            'status': estimate.get('StopStatus', 0),
                            'next_stop': estimate.get('NextBusTime'),
                            'crowding': estimate.get('CrowdingLevel', 0)
                        }
                        
                        arrival_times.append(arrival_info)
            
            # 根據預估時間排序，未發車的排在最後
            arrival_times.sort(key=lambda x: x['estimated_time'] if x['estimated_time'] > 0 else float('inf'))
            
            context.update({
                'stop_name': stop_name,
                'direction': direction,
                'arrival_times': arrival_times,
                'last_updated': datetime.now().strftime('%H:%M:%S')
            })
            
        except Exception as e:
            logger.error(f"查詢失敗: {str(e)}")
            context['error'] = f'查詢失敗：{str(e)}'
    
    return render(request, 'bus_search.html', context)

def update_arrivals(request):
    """AJAX 端點用於更新到站時間
    功能：
    1. 接收 AJAX 請求
    2. 更新指定站牌的到站時間
    3. 回傳 JSON 格式的更新結果
    """
    if request.method == 'POST':
        stop_name = request.POST.get('stop_name')
        direction = request.POST.get('direction')
        
        if not stop_name or direction is None:
            return JsonResponse({
                'success': False,
                'error': '請輸入站牌名稱並選擇方向'
            })
        
        try:
            token = get_access_token()
            stops_data = get_stop_info(token, stop_name)
            
            arrival_times = []
            processed_routes = set()
            
            for stop_route in stops_data:
                route_name = stop_route.get('RouteName', {}).get('Zh_tw', '')
                stop_name = stop_route.get('StopName', {}).get('Zh_tw', '')
                
                estimates = get_estimated_time(token, route_name, stop_name)
                
                for estimate in estimates:
                    est_direction = str(estimate.get('Direction'))
                    
                    route_key = f"{route_name}_{est_direction}"
                    if est_direction == direction and route_key not in processed_routes:
                        processed_routes.add(route_key)
                        
                        est_time = estimate.get('EstimateTime', 0)
                        if est_time is not None:
                            est_time = est_time // 60
                        else:
                            est_time = -1
                            
                        arrival_info = {
                            'route_name': route_name,
                            'stop_name': stop_name,
                            'estimated_time': est_time,
                            'plate_numb': estimate.get('PlateNumb', ''),
                            'status': estimate.get('StopStatus', 0)
                        }
                        
                        arrival_times.append(arrival_info)
            
            arrival_times.sort(key=lambda x: x['estimated_time'] if x['estimated_time'] > 0 else float('inf'))
            
            return JsonResponse({
                'success': True,
                'arrival_times': arrival_times,
                'last_updated': datetime.now().strftime('%H:%M:%S')
            })
            
        except Exception as e:
            logger.error(f"更新到站時間失敗: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': '無效的請求方法'})

def home(request):
    return render(request, "index.html")

def index(request):
    bus_data = None
    route_name = ''
    start_stop = ''
    end_stop = ''
    if request.method == 'POST':
        route_name = request.POST.get('route_name', '')
        bus_data, start_stop, end_stop = get_bus_data(route_name)
    user_count = User.objects.count()
    return render(request, 'index.html', {
        'bus_data': bus_data,
        'route_name': route_name,
        'start_stop': start_stop,
        'end_stop': end_stop,
        'user_count': user_count
    })

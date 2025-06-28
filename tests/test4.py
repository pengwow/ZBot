# import time
#
# import redis
#
# def get_evts():
#     currevts = []
#     idx = 0
#     while True:
#         currevt = redis.lpop('test')
#         if currevt is None:
#             break
#         currevts.append(currevt)
#         idx += 1
#         if idx >= 10:
#             break
#     return currevts, idx
#
# while True:
#     curr_evt, evts_len = get_evts()
#     if evts_len == 0:
#         time.sleep(1)
#         continue

eee = 'tJavIA6Q1STOZaOUlP6aOhjUfPBITgpG'


import copy
import numpy as np
from itertools import permutations
from collections import Counter

class Pose:             #长方体物品的姿态。一个长方体有3个对称面，可以横/直摆放，故有6种方式。
    wh_front = 0        #初始状态：width height 朝前，depth在侧，可以直观地理解为xyz轴
    hw_front = 1
    hd_front = 2
    dh_front = 3
    dw_front = 4
    wd_front = 5

class Axis:     #坐标轴
    x = 0
    y = 1
    z = 2

origin = [0, 0, 0]  #首个商品摆放在坐标轴的原点

class Item:
    def __init__(self, name, width, height, depth, weight=0, pose=0,position=origin):
        self.name = name
        self.width = width
        self.height = height
        self.depth = depth
        self.weight = weight
        self.pose = pose
        self.position = position
        self.volume = self.width * self.height * self.depth
        self.attr = (self.name,self.width,self.height,self.depth)

    def get_dimension(self):
        if self.pose == Pose.wh_front:
            d = [self.width, self.height, self.depth]
        elif self.pose == Pose.hw_front:
            d = [self.height, self.width, self.depth]
        elif self.pose == Pose.hd_front:
            d = [self.height, self.depth, self.width]
        elif self.pose == Pose.dh_front:
            d = [self.depth, self.height, self.width]
        elif self.pose == Pose.dw_front:
            d = [self.depth, self.width, self.height]
        elif self.pose == Pose.wd_front:
            d = [self.width, self.depth, self.height]
        else:
            d = []
        return d


class Bin:
    def __init__(self, name, width, height, depth, filling_ratio, max_weight):
        self.name = name
        self.width = width
        self.height = height
        self.depth = depth
        self.filling_ratio = filling_ratio
        self.max_weight = max_weight
        self.volume = self.width * self.height * self.depth
        self.items = []     #已放入的货品

    def init(self):
        self.items = []

    def get_total_weight(self):
        total_weight = 0
        for item in self.items:
            total_weight += item.weight
        return total_weight

    def put_item(self, item, position):
        fit = False
        item.position = position

        for i in range(6):
            item.pose = i
            d = item.get_dimension()
            if (self.width < position[0]+d[0] \
                or self.height < position[1]+d[1] \
                or self.depth < position[2]+d[2]):
                continue    #如果箱体某一边空余边长小于货品对应边长，说明按照这种旋转方式无法放入，进入下一循环

            fit = True

            for item_in in self.items:
                if space_collide(item_in, item):
                    fit = False
                    break

            if fit:         #如果没有空间重合，则判断载荷
                if self.get_total_weight() + item.weight > self.max_weight:
                    fit = False
                    return fit
                self.items.append(item)                             #记录加入的货品

            return fit
        return fit


class Packer:
    def __init__(self,mybin,myitems):
        self.bin = mybin
        self.items = myitems    #需要放入的全部货品

    def pack(self):
        first_fit = self.bin.put_item(self.items[0], origin)    
        if first_fit is False:     
            return

        for todo_item in self.items[1:]:
            for item_in in self.bin.items:                     #已经放入的货品
                for axis in range(3):
                    if axis == Axis.x:
                        pos = [
                            item_in.position[0] + item_in.get_dimension()[0],
                            item_in.position[1],
                            item_in.position[2]
                        ]
                    elif axis == Axis.y:
                        pos = [
                            item_in.position[0],
                            item_in.position[1] + item_in.get_dimension()[1],
                            item_in.position[2]
                        ]
                    elif axis == Axis.z:
                        pos = [
                            item_in.position[0],
                            item_in.position[1],
                            item_in.position[2] + item_in.get_dimension()[2]
                        ]
                    else:
                        print('error')
                        raise
                    fit = self.bin.put_item(todo_item, pos)
                    if fit:
                        break
                if fit:
                    break


#确保两货品的空间不“碰撞”
def space_collide(item1, item2):
    d1 = item1.get_dimension()          
    d2 = item2.get_dimension()          

    def dim_collide(item1, item2, axis):
        pj1 = item1.position[axis] + d1[axis]/2   #货品1的axis维度投影，加上该维度长的一半
        pj2 = item2.position[axis] + d2[axis]/2   #货品2的axis维度投影，加上该维度长的一半
        dis = abs(pj1 - pj2)                       #两者相减，代表对应维度上，两货品中点间的距离
        return dis < (d1[axis]+d2[axis])/2         #真，说明两货品在该维度的投影有重合。如果在三个维度的投影均有重合，说明空间碰撞。

    a = dim_collide(item1, item2, Axis.x)
    b = dim_collide(item1, item2, Axis.y)
    c = dim_collide(item1, item2, Axis.z)
    collision =  a and b and c

    return collision



#对堆叠场景的处理，例如面膜等较薄的物品，可以堆叠处理，效率更高
def stack(items):
    items = [copy.copy(e) for e in items]
    attrs = [item.attr for item in items]
    attr_qty = dict(Counter(attrs))

    def multi(v,bs):
        if type(v)!=str:
            v = v*bs
        return v

    for item_attr,qty in attr_qty.items():
        if qty >= 2:
            item_attr = list(item_attr)
            min_len = min(item_attr[1:])
            min_idx = item_attr.index(min_len)
            max_len = max(item_attr[1:])
            max_idx = item_attr.index(max_len)
            total_len = sum(item_attr[1:])
            mid_len = total_len - max_len - min_len
            ratio = int(mid_len/min_len)
            ratio3 = int(max_len/mid_len)
            if ratio >= 5:
                print('=====>',item_attr[0],'=====>作为较薄货品堆叠生效')
                ratio2 = int(qty/ratio)
                mod = qty%ratio
                items = [item for item in items if item.name!=item_attr[0]]
                if qty<=ratio:
                    item_attr[min_idx] = min_len * qty
                    new_item = Item(item_attr[0],item_attr[1],item_attr[2],item_attr[3],0)
                    items.append(new_item)
                else:
                    item_attr2 = copy.copy(item_attr)
                    item_attr2[min_idx] = min_len * mod
                    new_item = Item(item_attr2[0],item_attr2[1],item_attr2[2],item_attr2[3],0)
                    items.append(new_item)
                    item_attr[min_idx] = min_len * ratio
                    for i in range(ratio2):
                        items.append(Item(item_attr[0],item_attr[1],item_attr[2],item_attr[3],0))
            elif ratio < 5 and ratio3 >= 5 and qty >= 4:
                print('=====>',item_attr[0],'=====>作为细长货品堆叠生效')
                items = [item for item in items if item.name!=item_attr[0]]
                old_attr = copy.deepcopy(item_attr)
                bs = int(qty**0.5)
                item_attr = [multi(e,bs) for e in item_attr]
                item_attr[max_idx] = item_attr[max_idx]/bs
                new_item = Item(item_attr[0]+'+'*bs,item_attr[1],item_attr[2],item_attr[3],0)
                items.append(new_item)
                left = qty - bs**2
                old_item = Item(old_attr[0],old_attr[1],old_attr[2],old_attr[3],0)
                for i in range(left):
                    items.append(old_item)
                items = stack(items)
                # print([item.attr for item in items])
            elif ratio < 5 and ratio3 < 5 and qty >= 8:
                print('=====>',item_attr[0],'=====>作为普通货品堆叠生效')
                items = [item for item in items if item.name!=item_attr[0]]
                old_attr = copy.deepcopy(item_attr)
                bs = int(qty**(1/3))
                item_attr = [multi(e,bs) for e in item_attr]
                new_item = Item(item_attr[0]+'+'*bs,item_attr[1],item_attr[2],item_attr[3],0)
                items.append(new_item)
                left = qty - bs**3
                old_item = Item(old_attr[0],old_attr[1],old_attr[2],old_attr[3],0)
                for i in range(left):
                    items.append(old_item)
                items = stack(items)
                # print([item.attr for item in items])

    return items

#对放入顺序的搜索空间进行限制
def put_in_order(items):
    items.sort(key=lambda x:x.volume,reverse=True)
    if len(items)<=4:
        sample = list(permutations(items))
    elif len(items)<=9:
        sample = random.sample(list(permutations(items)), 24)
        sample.insert(0,items)
    else:       #10个物品以上，取样操作本身就会有效率问题，故直接取倒序
        sample = [items]
    return sample


def get_fit_box(items,bins):
    items = stack(items)
    sample = put_in_order(items)
    fit_boxes = {}
    goods_v = sum([item.volume for item in items])
    for bin in bins:
        bin_v = bin.volume
        if bin_v * bin.filling_ratio >= goods_v:
            l  = (bin.width,bin.height,bin.depth)   #对包装箱的初始摆放状态进行随机化
            for e in list(permutations(l)):
                bin.width,bin.height,bin.depth = e[0],e[1],e[2]
                for arr_items in sample:
                    bin.init()
                    packer = Packer(bin,arr_items)
                    packer.pack()
                    b = packer.bin
                    if len(b.items)==len(items):
                        ratio = goods_v/bin_v
                        fit_boxes[b.name] = round(ratio,2)
                        break
                if len(b.items)==len(items):
                    break
    return fit_boxes


##test
bin1 = Bin("Bin1", 40,30,30,1,100)
bin2 = Bin("Bin2", 60,35,50,1,100)
bin3 = Bin("Bin3", 20,15,10,1,100)
bins = [bin1,bin2,bin3]

item1 = Item("Item 1", 40,30,15)
item2 = Item("Item 2", 40,30,10)
item3 = Item("Item 3", 2,40,30)
item4 = Item("Item 4", 3,40,30)
items = [item1,item2,item3,item4]

if __name__ == '__main__':
    fit_boxes = get_fit_box(items,bins)
    print(fit_boxes)






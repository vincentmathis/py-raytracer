#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from math import sqrt, tan
from PIL import Image


class Vector(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return 'Vector(%s,%s,%s)' % (self.x, self.y, self.z)

    def __add__(self, other):
        if type(other) is type(self):
            return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    __radd__ = __add__

    def __sub__(self, other):
        if type(other) is type(self):
            return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    __rsub__ = __sub__

    def __mul__(self, other):
        if type(other) is int or type(other) is float:
            return Vector(self.x * other, self.y * other, self.z * other)

    __rmul__ = __mul__

    def __truediv__(self, other):
        if type(other) is int or type(other) is float:
            if other is not 0:
                return Vector(self.x / other, self.y / other, self.z / other)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        return Vector(self.y * other.z - other.y * self.z,
                      self.x * other.z - other.x * self.z,
                      self.x * other.y - other.x * self.y)

    def magnitude(self):
        return sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalized(self):
        mag = self.magnitude()
        return Vector(self.x / mag, self.y / mag, self.z / mag)

    def scale(self, other):
        return self.__mul__(other)

    def tuple(self):
        return int(self.x), int(self.y), int(self.z)


class Ray(object):
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction.normalized()

    def __repr__(self):
        return 'Ray(%s,%s)' % (repr(self.origin), self.direction)

    def point_at_param(self, t):
        return self.origin + self.direction.scale(t)


class Sphere(object):
    def __init__(self, center, radius, material):
        self.center = center
        self.radius = radius
        self.material = material

    def __repr__(self):
        return 'Sphere(%s,%s)' % (repr(self.center), self.radius)

    def intersec_param(self, ray):
        co = self.center - ray.origin
        v = co.dot(ray.direction)
        discriminant = v * v - co.dot(co) + self.radius * self.radius
        if discriminant:
            if discriminant < 0:
                return None
            else:
                return v - sqrt(discriminant)

    def normal_at(self, p):
        return (p - self.center).normalized()


class Plane(object):
    def __init__(self, point, normal, material):
        self.point = point
        self.normal = normal.normalized()
        self.material = material

    def __repr__(self):
        return 'Plane(%s,%s)' % (repr(self.point), repr(self.normal))

    def intersec_param(self, ray):
        op = ray.origin - self.point
        a = op.dot(self.normal)
        b = ray.direction.dot(self.normal)
        if b:
            return -a / b
        else:
            return None

    def normal_at(self, p):
        return self.normal


class Triangle(object):
    def __init__(self, a, b, c, material):
        self.a = a
        self.b = b
        self.c = c
        self.u = self.b - self.a
        self.v = self.c - self.a
        self.material = material

    def __repr__(self):
        return 'Triangle(%s,%s,%s)' % (repr(self.a), repr(self.b), repr(self.c))

    def intersec_param(self, ray):
        w = ray.origin - self.a
        dv = ray.direction.cross(self.v)
        dvu = dv.dot(self.u)
        if dvu == 0.0:
            return None
        wu = w.cross(self.u)
        r = dv.dot(w) / dvu
        s = wu.dot(ray.direction) / dvu
        if 0 <= r <= 1 and 0 <= s <= 1 and r + s <= 1:
            print(wu.dot(self.v) / dvu)
            return -wu.dot(self.v) / dvu
        else:
            return None
        # n = self.u.cross(self.v).normalized()
        # d = n.dot(self.a)
        # t = (n.dot(ray.origin) + d) / n.dot(ray.direction)
        # if t < 0:
        #     return None
        # p = ray.point_at_param(t)
        # if n.dot((self.b - self.a).cross(p - self.a)) < 0:
        #     return None
        # if n.dot((self.c - self.b).cross(p - self.b)) < 0:
        #     return None
        # if n.dot((self.a - self.c).cross(p - self.c)) < 0:
        #     return None
        # return t

    def normal_at(self, p):
        return self.u.cross(self.v).normalized()


class Material(object):
    def __init__(self, base_color, ambient_c, diffuse_c, specular_c, specular_k, reflect_c):
        self.base_color = base_color
        self.ambient_c = ambient_c
        self.diffuse_c = diffuse_c
        self.specular_c = specular_c
        self.specular_k = specular_k
        self.reflect_c = reflect_c

    def color_at(self, p):
        return self.base_color


class CheckerboardMaterial(object):
    def __init__(self, base_color, other_color, checker_size):
        self.base_color = base_color
        self.other_color = other_color
        self.checker_size = checker_size
        self.ambient_c = 0.5
        self.diffuse_c = 0.6
        self.specular_c = 0.2
        self.specular_k = 4
        self.reflect_c = 0

    def color_at(self, p):
        p = p.scale(1.0 / self.checker_size)
        if (int(abs(p.x) + 0.5) + int(abs(p.y) + 0.5) + int(abs(p.z) + 0.5)) % 2:
            return self.other_color
        return self.base_color


class Light(object):
    def __init__(self, center, color):
        self.center = center
        self.color = color


class Camera(object):
    def __init__(self, e, c, up, fov, a_ratio):
        self.e = e
        self.c = c
        self.up = up
        self.fov = fov
        self.f = (self.c - self.e) / (self.c - self.e).magnitude()
        self.s = self.f.cross(up) / self.f.cross(up).magnitude()
        self.u = self.s.cross(self.f)
        self.height = 2 * tan(self.fov / 2)
        self.width = a_ratio * self.height


class Scene(object):
    def __init__(self, camera, img_width, img_height, max_level, object_list, light):
        self.camera = camera
        self.img_width = img_width
        self.img_height = img_height
        self.max_level = max_level
        self.BACKGROUND_COLOR = Vector(50, 50, 50)
        self.object_list = object_list
        self.light = light

    def calc_ray(self, x, y):
        pxl_width = self.camera.width / (self.img_width - 1)
        pxl_height = self.camera.height / (self.img_height - 1)
        x_comp = self.camera.s.scale(x * pxl_width - self.camera.width / 2)
        y_comp = self.camera.u.scale(y * pxl_height - self.camera.height / 2)
        return Ray(self.camera.e, self.camera.f + x_comp + y_comp)

    def trace_ray(self, level, ray, ignore=None):
        hitpoint_data = self.intersect(level, ray, ignore=ignore)
        if hitpoint_data:
            return self.shade(level, hitpoint_data)
        return self.BACKGROUND_COLOR

    def intersect(self, level, ray, ignore=None):
        if level >= self.max_level:
            return None
        max_dist = float('inf')
        nearest_obj = None
        for object in self.object_list:
            if object is not ignore:
                hit_dist = object.intersec_param(ray)
                if hit_dist:
                    if 0 < hit_dist < max_dist:
                        max_dist = hit_dist
                        nearest_obj = object
        if nearest_obj:
            point = ray.point_at_param(max_dist)
            return nearest_obj, ray, point, nearest_obj.normal_at(point)
        else:
            return None

    def shade(self, level, hitpoint_data):
        object, ray, point, normal = hitpoint_data
        direct_color = self.compute_direct_light(hitpoint_data)
        reflected_ray = self.compute_reflected_ray(hitpoint_data)
        reflect_color = self.trace_ray(level + 1, reflected_ray, ignore=object)
        return direct_color + reflect_color * object.material.reflect_c

    def compute_direct_light(self, hitpoint_data):
        object, ray, point, normal = hitpoint_data
        color = object.material.color_at(point)
        ambient_color = color * object.material.ambient_c
        hitpoint_data_shadow = self.intersect(0, Ray(point, self.light.center - point), ignore=object)
        if hitpoint_data_shadow:
            return ambient_color
        l = (self.light.center - point).normalized()
        # TODO warum -l?
        lr = (2 * normal.dot(l) * normal - l).normalized()
        d = ray.direction.normalized()
        # TODO Ca statt Cin für diffuse
        diffuse_color = color * object.material.diffuse_c * max(normal.dot(l), 0)
        specular_color = self.light.color * object.material.specular_c * max(-d.dot(lr),
                                                                             0) ** object.material.specular_k
        return ambient_color + diffuse_color + specular_color

    def compute_reflected_ray(self, hitpoint_data):
        object, ray, point, normal = hitpoint_data
        return Ray(point, ray.direction - 2 * normal.dot(ray.direction) * normal)

    def render(self):
        image = Image.new('RGB', (self.img_width, self.img_height))
        for x in range(self.img_width):
            for y in range(self.img_height):
                ray = self.calc_ray(x, y)
                color = self.trace_ray(0, ray)
                image.putpixel((x, y), color.tuple())
        image.save('render.png', 'PNG')
        image.show()


def main(args):
    img_width = 512
    img_height = 512
    fov = 45
    aspect_ratio = img_width / img_height
    trace_depth = 3

    red = Material(Vector(255, 0, 0), 0.2, 0.5, 0.5, 32, 0.3)
    green = Material(Vector(0, 255, 0), 0.2, 0.5, 0.5, 32, 0.3)
    blue = Material(Vector(0, 0, 255), 0.2, 0.5, 0.5, 32, 0.3)
    yellow = Material(Vector(255, 255, 0), 0.2, 0.5, 0.5, 32, 0.3)
    grey = Material(Vector(150, 150, 150), 0.2, 0.5, 0.5, 32, 0.3)
    checker = CheckerboardMaterial(Vector(255, 255, 255), Vector(0, 0, 0), 2)

    sphere_green = Sphere(Vector(-2, 2, 0), 1.5, green)
    sphere_red = Sphere(Vector(2, 2, 0), 1.5, red)
    sphere_blue = Sphere(Vector(0, 5.5, 0), 1.5, blue)
    plane = Plane(Vector(0, -0.5, 0), Vector(0, 1, 0), checker)
    triangle = Triangle(Vector(-2, 2, 0), Vector(2, 2, 0), Vector(0, 5.5, 0), yellow)

    light = Light(Vector(30, 30, 10), Vector(210, 210, 200))
    object_list = [sphere_red, sphere_green, sphere_blue, plane]

    camera = Camera(Vector(0, 3.75, 10), Vector(0, 3.75, 0), Vector(0, 1, 0), fov, aspect_ratio)
    scene = Scene(camera, img_width, img_height, trace_depth, object_list, light)
    scene.render()


if __name__ == '__main__':
    main(sys.argv[1:])

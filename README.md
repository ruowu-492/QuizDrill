# `该项目的第一个版本尚在开发中`
## 项目目标

该项目基于JSON题库向用户提供刷题服务，提供多种刷题模式，最终形态为基于Felt框架的跨平台GUI程序。
## 项目功能
* 多种刷题模式
  * 顺序刷题
  * 只刷新题
  * 只刷错题
  * 模拟考试
  * 背题模式
* 通过率预测
* 以折线显示考试记录
## 项目结构
* src - 源码
  * assrts - 静态资源
    * data - 数据资源
  * core - 后端实现
    * \_\_init\_\_.py 
    * QuesServ.py - 出题和数据管理
  * ui - 前端实现
    * \_\_init\_\_.py 
  * main.py
* tests - 测试脚本
* utils - 辅助脚本
  * geneTestQuestion.py - 生成测试题库
* README.md

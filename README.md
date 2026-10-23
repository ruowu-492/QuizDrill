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

[放几只鸽子?]
* 以折线显示考试记录
* 多题库适配
* 多用户适配
* 开源题库社区(?)

## 项目结构
* src - 源码
  * assrts - 静态资源
    * SourceHanSansSC-Regular.otf - 中文字体 
    * question.json - 题库
  * core - 后端实现
    * \_\_init\_\_.py 
    * QuesServ.py - 出题和数据管理
  * ui - 前端实现
    * \_\_init\_\_.py
    * AnsQuesPage.py - 答题页
    * Custom.py - 自定义控件
    * HomePahe.py - 主页
  * main.py - 主程序入口
  * main_conse.py - 控制台版本入口
* tests - 测试脚本
* utils - 辅助脚本
  * geneTestQuestion.py - 生成测试题库
* README.md

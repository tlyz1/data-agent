from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class DwMysqlRepository:
    #实现模拟数据仓库（dw库）的读写操作
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_column_types(self, table_name:str)->dict[str,str]:
        """
        根据表查询表中所有字段的类型

        :param table_name:
        :return: {'字段名':'字段类型'，'字段名':'字段类型'}
        """
        # 定义sql语句
        sql = f"show columns from  {table_name}"
        # 执行sql
        result=await self.session.execute(text(sql))
        #获取结果 [(row(Field=order_id,Type=varchar)),(),()]
        return {row.Field: row.Type for row in result.fetchall()}

    async def get_column_values(self, table_name: str, column_name: str, limit: int = 10):
        """
        查询字段值
        :param table_name:
        :param column_name:
        :return:
        """
        sql =f"select distinct {column_name} from {table_name} limit {limit}"

        result=await self.session.execute(text(sql))
        return result.scalars().fetchall()


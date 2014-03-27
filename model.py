from sqlalchemy import (Column,
						ForeignKey,
						event,
						Index,
						Table,
						types,
						Unicode,
						select,
						func,
						case)

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import synonym
from sqlalchemy.sql.expression import func

from zope.sqlalchemy import ZopeTransactionExtension 

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Category(Base):
	__tablename__= 'categories'
	__mapper_args__ = {'batch': False  # allows extension to fire for each
					# instance before going to the next.
					}
	parent = None
	id = Column(types.Integer(), primary_key=True)
	name = Column(types.Unicode(100))
	level = Column("lvl", types.Integer, nullable=False)
	left = Column("lft", types.Integer, nullable=False)
	right = Column("rgt", types.Integer, nullable=False) 

@event.listens_for(Category, "before_insert")
def before_insert(mapper, connection, instance):
	
	print 'making adjustments before insertion'
	#If the new term has no parent, connect to root
	if instance.parent == None:
		category = mapper.mapped_table
		values = connection.execute(select([category]).where(category.c.name == 'TREE_ROOT')).first().values()
		parent = Category()
		parent.name = values[0]
		parent.level = values[2]
		parent.left = values[3]
		parent.right = values[4]
		instance.parent = parent
	category = mapper.mapped_table
	
	#Find right most sibling's right value
	right_most_sibling = connection.scalar(
		select([category.c.rgt]).
			where(category.c.name == instance.parent.name)
	)
	
	#Update all values greater than rightmost sibiling
	connection.execute(
		category.update(
			category.c.rgt >= right_most_sibling).values(
				
				#Update if left bound in greater than rightmost sibling
				lft=case(
					[(category.c.lft > right_most_sibling,
						category.c.lft + 2)],
					else_=category.c.lft
				),
				#Update if right bound is greater than right most sibling
				rgt=case(
					[(category.c.rgt >= right_most_sibling,
							category.c.rgt + 2)],
						else_=category.c.rgt
				  )
		)
	)
	instance.left = right_most_sibling
	instance.right = right_most_sibling + 1
	instance.level  = instance.parent.level + 1
		
@event.listens_for(Category, "after_delete")
def after_delete(mapper, connection, target):
	
	
	category = mapper.mapped_table
	#Delete leaf
	if target.right-target.left == 1:
		print 'updating after deletion of leaf'
		#Update all values greater than right side
		connection.execute(
			category.update(
				category.c.rgt > target.left).values(
					
					#Update if left bound in greater than right side
					lft=case(
						[(category.c.lft > target.left,
							category.c.lft - 2)],
						else_=category.c.lft
					),
					#Update if right bound is greater than right
					rgt=case(
						[(category.c.rgt >= target.left,
								category.c.rgt - 2)],
							else_=category.c.rgt
					  )
			)
		)
	#Delete parent
	else:
		print 'updating after deletion of parent'
		category = mapper.mapped_table
		
		#Promote all children
		connection.execute(
			category.update(
				category.c.lft.between(target.left, target.right)).values(
					
					#Update if left bound in greater than right side
					lft=case(
						[(category.c.lft > target.left,
							category.c.lft - 1)],
						else_=category.c.lft
					),
					#Update if right bound is greater than right
					rgt=case(
						[(category.c.rgt > target.left,
								category.c.rgt - 1)],
							else_=category.c.rgt
					 ),
					lvl=case([(category.c.lvl > target.level,
								category.c.lvl - 1)],
							else_=category.c.lvl
					)
			)
		)
		
		#Update all values greater than right side
		connection.execute(
			category.update(
				category.c.rgt > target.right).values(
					
					#Update if left bound in greater than right side
					lft=case(
						[(category.c.lft > target.left,
							category.c.lft - 2)],
						else_=category.c.lft
					),
					#Update if right bound is greater than right
					rgt=case(
						[(category.c.rgt >= target.left,
								category.c.rgt - 2)],
							else_=category.c.rgt
					  )
			)
		)

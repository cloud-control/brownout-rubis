package edu.rice.rubis.beans;

import java.net.URLEncoder;
import java.rmi.*;
import javax.ejb.*;
import javax.rmi.PortableRemoteObject;
import javax.naming.InitialContext;

/**
 * CategoryBean is an entity bean with "container managed persistence". 
 * The state of an instance is stored into a relational database. 
 * The following table should exist:<p>
 * <pre>
 * CREATE TABLE categories (
 *    id   INTEGER UNSIGNED NOT NULL UNIQUE,
 *    name VARCHAR(50),
 *    PRIMARY KEY(id)
 * );
 * </pre>
 * @author <a href="mailto:cecchet@rice.edu">Emmanuel Cecchet</a> and <a href="mailto:julie.marguerite@inrialpes.fr">Julie Marguerite</a>
 * @version 1.0
 */

public class CategoryBean implements EntityBean 
{
  private EntityContext entityContext;
  private transient boolean isDirty; // used for the isModified function

  /* Class member variables */

  public Integer id;
  public String  name;


  /**
   * Get category's id.
   *
   * @return category id
   * @exception RemoteException if an error occurs
   */
  public Integer getId() throws RemoteException
  {
    return id;
  }

  /**
   * Get the category name.
   *
   * @return category name
   * @exception RemoteException if an error occurs
   */
  public String getName() throws RemoteException
  {
    return name;
  }

  /**
   * Set category's name
   *
   * @param newName category name
   * @exception RemoteException if an error occurs
   */
  public void setName(String newName) throws RemoteException 
  {
    name = newName;
    isDirty = true; // the bean content has been modified
  }


  /**
   * This method is used to create a new Category Bean. Note that the category
   * id is automatically generated by the database (AUTO_INCREMENT) on the
   * primary key.
   *
   * @param categoryName Category name
   *
   * @return pk primary key set to null
   * @exception CreateException if an error occurs
   * @exception RemoteException if an error occurs
   * @exception RemoveException if an error occurs
   */
  public CategoryPK ejbCreate(String categoryName) throws CreateException, RemoteException, RemoveException
  {
      // Connecting to IDManager Home interface thru JNDI
      IDManagerHome home = null;
      IDManager idManager = null;
      
      try 
      {
        InitialContext initialContext = new InitialContext();
        home = (IDManagerHome)PortableRemoteObject.narrow(initialContext.lookup(
               "java:comp/env/ejb/IDManager"), IDManagerHome.class);
      } 
      catch (Exception e)
      {
        throw new EJBException("Cannot lookup IDManager: " +e);
      }
     try 
      {
        IDManagerPK idPK = new IDManagerPK();
        idManager = home.findByPrimaryKey(idPK);
        id = idManager.getNextCategoryID();
        name = categoryName;
      } 
      catch (Exception e)
      {
        throw new EJBException("Cannot create category: " +e);
      }
      return null; 
  }


  /** This method just set an internal flag to 
      reload the id generated by the DB */
  public void ejbPostCreate(String categoryName)
  {
    isDirty = true; // the id has to be reloaded from the DB
  }

  /** Persistence is managed by the container and the bean
      becomes up to date */
  public void ejbLoad() throws RemoteException 
  {
    isDirty = false;
  }

  /** Persistence is managed by the container and the bean
      becomes up to date */
  public void ejbStore() throws RemoteException
  {
    isDirty = false;
  }

  /** This method is empty because persistence is managed by the container */
  public void ejbActivate() throws RemoteException {}
  /** This method is empty because persistence is managed by the container */
  public void ejbPassivate() throws RemoteException {}
  /** This method is empty because persistence is managed by the container */
  public void ejbRemove() throws RemoteException, RemoveException {}

  /**
   * Sets the associated entity context. The container invokes this method 
   *  on an instance after the instance has been created. 
   * 
   * This method is called in an unspecified transaction context. 
   * 
   * @param context - An EntityContext interface for the instance. The instance should 
   *              store the reference to the context in an instance variable. 
   * @exception EJBException  Thrown by the method to indicate a failure 
   *                          caused by a system-level error.
   * @exception RemoteException - This exception is defined in the method signature
   *                           to provide backward compatibility for enterprise beans
   *                           written for the EJB 1.0 specification. 
   *                           Enterprise beans written for the EJB 1.1 and 
   *                           higher specification should throw the javax.ejb.EJBException 
   *                           instead of this exception. 
   */
  public void setEntityContext(EntityContext context) throws RemoteException
  {
    entityContext = context;
  }

  /**
   * Unsets the associated entity context. The container calls this method 
   *  before removing the instance. This is the last method that the container 
   *  invokes on the instance. The Java garbage collector will eventually invoke 
   *  the finalize() method on the instance. 
   *
   * This method is called in an unspecified transaction context. 
   * 
   * @exception EJBException  Thrown by the method to indicate a failure 
   *                          caused by a system-level error.
   * @exception RemoteException - This exception is defined in the method signature
   *                           to provide backward compatibility for enterprise beans
   *                           written for the EJB 1.0 specification. 
   *                           Enterprise beans written for the EJB 1.1 and 
   *                           higher specification should throw the javax.ejb.EJBException 
   *                           instead of this exception.
   */
  public void unsetEntityContext() throws RemoteException
  {
    entityContext = null;
  }

  /**
   * Display category information for the BrowseCategories servlet
   *
   * @return a <code>String</code> containing HTML code
   * @exception RemoteException if an error occurs
   * @since 1.0
   */
  public String printCategory() throws RemoteException
  {
    return "<a href=\"/servlet/edu.rice.rubis.beans.servlets.SearchItemsByCategory?category="+id+
                  "&categoryName="+URLEncoder.encode(name)+"\">"+name+"</a><br>\n";
  }

  /**
   * Display category information for the BrowseCategories servlet
   *
   * @return a <code>String</code> containing HTML code
   * @exception RemoteException if an error occurs
   * @since 1.0
   */
  public String printCategoryByRegion(int regionId) throws RemoteException
  {
    return "<a href=\"/servlet/edu.rice.rubis.beans.servlets.SearchItemsByRegion?category="+id+
      "&categoryName="+URLEncoder.encode(name)+"&region="+regionId+"\">"+name+"</a><br>\n";
  }


  /**
   * Returns true if the beans has been modified.
   * It prevents the EJB server from reloading a bean
   * that has not been modified.
   *
   * @return a <code>boolean</code> value
   */
  public boolean isModified() 
  {
    return isDirty;
  }


  /**
   * Display category information for the BrowseCategories servlet
   *
   * @return a <code>String</code> containing HTML code
   * @exception RemoteException if an error occurs
   * @since 1.0
   */
  public String printCategoryToSellItem(int userId) throws RemoteException
  {
    return "<a href=\"/servlet/edu.rice.rubis.beans.servlets.SellItemForm?category="+id+"&user="+userId+"\">"+name+"</a><br>\n";
  }
}

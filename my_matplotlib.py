import colors
import numpy as np
import matplotlib.figure as Figure
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import matplotlib.transforms as mtransforms
import math

class SimplePlot:
    def __init__(self):
        self.fig = plt.figure()
        
class PlotSomething(object):
    def __init__(self,x,x_label='x_label',y_label='y_label',window_title='Figure Title'):
        self.x = x
        self.fig = plt.figure(figsize=(18,12))
        self.fig.canvas.set_window_title(window_title)
        #self.ax = self.fig.add_subplot(111)
        self.ax = plt.axes([0.1, 0.2, 0.75, 0.75]) #left,bottom,width,height
        self.ax.set_title(window_title)
        self.ax_table = plt.axes([0.1,0.0,0.85,0.1])
        self.ax_table.set_axis_off()
        self.cname_list = ['blue','red','green','orange','brown','purple','cyan','pink','lime','peachpuff','chocolate','lavender',\
                           'azure','crimson','teal','coral','saddlebrown','plum','slateblue','palevioletred','thistle','olive',\
                           'darkorange','wheat','orchid']*4
        self.rgb_color_list = [ colors.colorConverter.to_rgb(color_name) for color_name in self.cname_list ] 
        self.color_list = [ colors.hex2color(colors.rgb2hex(a_color)) for a_color in self.rgb_color_list ]
        self.marker_list = ['o','^','s','v','d','+','x','o','^','s','v','d','+','x','o','^','s','v','d','+','x']*4
        if type([]) == type(x[0]): self.num_series=len(x)
        else: self.num_series=1
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
    def set_y_axis(self,lo_limit,hi_limit):
        self.ax.set_ylim(lo_limit,hi_limit)
        self.update_changes()
    def set_x_axis(self,lo_limit,hi_limit):
        self.ax.set_xlim(lo_limit,hi_limit)
        self.update_changes()
    def set_xtick_names(self,xtick_labels,Rotation=45,FontSize=8):
        xtickNames = plt.setp(self.ax,xticklabels=xtick_labels)
        plt.setp(xtickNames,rotation=Rotation,fontsize=FontSize)
    def add_legend(self,legend_list=[],legend_loc='upper right'):
        if len(legend_list)>0: self.legend = self.ax.legend(legend_list,loc=legend_loc)
        else: self.legend = self.ax.legend()
        self.legend.set_picker(True)  #only works if frameon is True, which is default in ax.legend call
        self.legend.draggable(True)
        self.update_changes()
    def add_table(self,cellText,rowLabels,colLabels,loc='center'):
        self.the_table = self.ax_table.table(cellText = cellText,rowLabels=rowLabels,colLabels=colLabels,loc=loc)
        self.update_changes()
    def update_changes(self):
        plt.draw()


class MakeHistogramPlot(PlotSomething):
    def __init__(self,x,lo_limit,hi_limit,do_normalize=True,x_label='x_label',y_label='y_label',legend_list=[],window_title='Histogram Title'):
        super(MakeHistogramPlot,self).__init__(x,x_label,y_label,window_title)
        if self.num_series == 1: self.n,self.bins,self.patches = self.ax.hist(x,200,range=[lo_limit,hi_limit],normed=do_normalize,facecolor='green',alpha=0.75) 
        else: self.n,self.bins,self.patches = self.ax.hist(x,200,normed=do_normalize,range=[lo_limit,hi_limit],histtype='bar',color=self.color_list[:self.num_series],label=legend_list)
        self.ax.set_xlim(lo_limit,hi_limit)
        if self.num_series>1: 
            #self.add_legend(legend_list,legend_loc)
            HistList = []
            for a_n in self.n: HistList += a_n.tolist()
            self.ax.set_ylim(0,max(HistList)*1.1)
        else: self.ax.set_ylim(0,max(self.n.tolist())*1.1)
        self.ax.grid(True)

class MakeScatterPlot(PlotSomething):
    def __init__(self,y,x,lo_limit,hi_limit,x_label='x_label',y_label='y_label',legend_list=['']*32,legend_loc='upper right',window_title='Scatter Plot Title',xtick_labels=[]):
        super(MakeScatterPlot,self).__init__(y,x_label,y_label,window_title)
        self.ax.set_xlim(lo_limit,hi_limit)
        if self.num_series>1:
            series_range = range(self.num_series-1,-1,-1)
            for i in series_range: self.ax.scatter(x[i],y[i],c=self.color_list[i],marker=self.marker_list[i],label=legend_list[i])
            self.add_legend([ legend_list[i] for i in xrange(self.num_series-1,-1,-1)],legend_loc)
            #self.add_legend(legend_list,legend_loc)
        else: self.ax.scatter(x,y)
        self.ax.xaxis.set_ticks(x[0],minor=True)
        if len(xtick_labels)>0: 
            self.ax.set_xticklabels(xtick_labels,minor=True,rotation='vertical',fontsize=8)
            self.set_xtick_names(xtick_labels,Rotation='vertical',FontSize=8)
        self.ax.xaxis.grid(True,linestyle='-',which='both',color='lightgrey',alpha=0.5)
        self.ax.yaxis.grid(True,linestyle='-',which='major', color='lightgrey',alpha=0.5)

class MakeBoxPlot(PlotSomething):
    '''Make a box and whisker plot for each column of *x* or each
    vector in sequence *x*.  The box extends from the lower to
    upper quartile values of the data, with a line at the median.
    The whiskers extend from the box to show the range of the
    data.  Flier points are those past the end of the whiskers.
    *bootstrap* (default None) specifies whether to bootstrap the
    confidence intervals around the median for notched
    boxplots. If bootstrap==None, no bootstrapping is performed,
    and notches are calculated using a Gaussian-based asymptotic
    approximation (see McGill, R., Tukey, J.W., and Larsen, W.A.,
    1978, and Kendall and Stuart, 1967). Otherwise, bootstrap
    specifies the number of times to bootstrap the median to
    determine it's 95% confidence intervals. Values between 1000
    and 10000 are recommended.
    '''
    def __init__(self,x,x_label='x_label',y_label='y_label',box_color='blue',whisker_color='blue',line_style='-',window_title='BoxPlot Title',box_notch=1,boot_strap=None):
        super(MakeBoxPlot,self).__init__(x,x_label,y_label,window_title)
        pos = np.array(range(len(x)))+1
        self.bp = self.ax.boxplot(x,sym='k+', patch_artist=True,positions=pos,notch=box_notch,bootstrap=boot_strap)
        self.ax.yaxis.grid(True,linestyle='-',which='major', color='lightgrey',alpha=0.5)
        if self.num_series==1: 
            plt.setp(self.bp['boxes'], color=box_color)
        else: 
            aRange = range(self.num_series)
            for i in aRange: 
                plt.setp(self.bp['boxes'][i], color=self.color_list[i])
        plt.setp(self.bp['whiskers'], color=whisker_color, linestyle=line_style )
        plt.setp(self.bp['fliers'], markersize=3.0)


class AnnoteFinder:
  """
  callback for matplotlib to display an annotation when points are clicked on.  The
  point which is closest to the click and within xtol and ytol is identified.
    
  Register this function like this:
    
  scatter(xdata, ydata)
  af = AnnoteFinder(xdata, ydata, annotes)
  connect('button_press_event', af)
  """

  def __init__(self, xdata, ydata, annotes, axis=None, xtol=None, ytol=None):
    self.data = zip(xdata, ydata, annotes)
    if xtol is None:
      xtol = ((max(xdata) - min(xdata))/float(len(xdata)))/2
    if ytol is None:
      ytol = ((max(ydata) - min(ydata))/float(len(ydata)))/2
    self.xtol = xtol
    self.ytol = ytol
    if axis is None:
      self.axis = plt.gca()
    else:
      self.axis= axis
    self.drawnAnnotations = {}
    self.links = []

  def distance(self, x1, x2, y1, y2):
    """
    return the distance between two points
    """
    return math.hypot(x1 - x2, y1 - y2)

  def __call__(self, event):
    if event.inaxes:
      clickX = event.xdata
      clickY = event.ydata
      if self.axis is None or self.axis==event.inaxes:
        annotes = []
        for x,y,a in self.data:
          if  clickX-self.xtol < x < clickX+self.xtol and  clickY-self.ytol < y < clickY+self.ytol :
            annotes.append((self.distance(x,clickX,y,clickY),x,y, a) )
        if annotes:
          annotes.sort()
          distance, x, y, annote = annotes[0]
          self.drawAnnote(event.inaxes, x, y, annote)
          for l in self.links:
            l.drawSpecificAnnote(annote)

  def drawAnnote(self, axis, x, y, annote):
    """
    Draw the annotation on the plot
    """
    if (x,y) in self.drawnAnnotations:
      markers = self.drawnAnnotations[(x,y)]
      for m in markers:
        m.set_visible(not m.get_visible())
      self.axis.figure.canvas.draw()
    else:
      t = axis.text(x,y, "(%3.2f, %3.2f) - %s"%(x,y,annote), )
      m = axis.scatter([x],[y], marker='d', c='r', zorder=100)
      self.drawnAnnotations[(x,y)] =(t,m)
      self.axis.figure.canvas.draw()

  def drawSpecificAnnote(self, annote):
    annotesToDraw = [(x,y,a) for x,y,a in self.data if a==annote]
    for x,y,a in annotesToDraw:
      self.drawAnnote(self.axis, x, y, a)

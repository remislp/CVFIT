
from scipy import stats
import numpy as np

class Hill(object):
    def __init__(self, eqname, pars=None):
        """
        pars = [Ymin, Ymax, EC50, nH]
        """
        self.eqname = eqname
        self.pars = pars
        self.fixed = []
        self.names = ['Ymin', 'Ymax', 'EC50', 'nH  ']
        self.data = None
        self.guess = None
        self._theta = None

        
    def equation(self, conc, coeff):
        '''
        The hill equation.
        '''
        return (coeff[0] + (coeff[1] * (conc / coeff[2]) ** coeff[3]) / 
            (1 + (conc / coeff[2]) ** coeff[3]))
            
    def to_fit(self, theta, conc):
        #for each in np.nonzero(self.fixed)[0]:   
        #    theta = np.insert(theta, each, self.pars[each])
        self._set_theta(theta)
        return self.equation(conc, self.pars)
    
    def _set_theta(self, theta):
        for each in np.nonzero(self.fixed)[0]:   
            theta = np.insert(theta, each, self.pars[each])
        self.pars = theta
    def _get_theta(self):
        return self.pars[np.nonzero(np.invert(self.fixed))[0]]
    theta = property(_get_theta, _set_theta)
    
    def normalise(self, data):
        '''
        Nomalise Y to the fitted maximum.
        '''

        if data.trend == 1:
            # Nomalise the coefficients by fixing the Y(0) and Ymax
            self.normpars = self.pars.copy()
            self.normpars[0], self.normpars[1] = 0, 1
            # Nomalise the response
            data.normY = (data.Y - self.pars[0]) / self.pars[1]
        elif data.trend == -1:
            # Nomalise the coefficients by fixing the Y(0) and Ymax
            self.normpars = self.pars.copy()
            self.normpars[0], self.normpars[1] = 1, 0
            # Nomalise the response
            data.normY = 1 - (data.Y - self.pars[1]) / self.pars[0]
    
    def propose_guesses(self, data):
        '''
        Calculate the initial guesses for fitting with Hill equation.
        '''
        
        #if self.Component == 1:
        self.guess = np.empty(4)
        slope, intercept, r_value, p_value, std_err = stats.linregress(data.X, data.Y)
        if slope > 0:
            data.trend = 1
        else:
            data.trend = -1
        if data.trend == 1: # Response increases with concentration
            # Determine Y(0)
            if self.fixed[0]:
                self.guess[0] = 0
            else:
                self.guess[0] = np.mean(data.Y[data.X == data.X[0]])
            if self.fixed[1]:
                self.guess[1] = 1
            else:
                # Determine Ymax
                self.guess[1] = np.mean(data.Y[data.X == data.X[-1]]) - self.guess[0]
        else: # Response decreases with concentration
            # Determine Y(0)
            self.guess[0] = np.mean(data.Y[data.X == data.X[-1]])
            # Determine Ymin
            self.guess[1] = np.mean(data.Y[data.X == data.X[0]]) - self.guess[0]
        # Determine Kr
        self.guess[2] = 10 ** ((np.log10(data.X[0]) + np.log10(data.X[-1])) / 2)
        # Determine nH  
        LinRegressX = np.log10(data.X[data.Y < np.amax(data.Y)]) - np.log10(self.guess[2])
        ratio = data.Y[data.Y < np.amax(data.Y)] / np.amax(data.Y)
        LinRegressY = np.log10(ratio / (1 - ratio))
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            LinRegressX, LinRegressY)
        self.guess[3] = slope

#        elif self.Component == 2:
#            print 'Two Components fitting is not completed.'
#            sys.exit(0)
        self.pars = self.guess.copy()
        #return self.guess


import { useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Settings2, Palette, Activity, Bell, Shield, Database, Save, Info } from 'lucide-react';

export function Settings() {
  // General Settings
  const [autoSave, setAutoSave] = useState(true);
  const [showTutorials, setShowTutorials] = useState(true);
  
  // Appearance Settings
  const [theme, setTheme] = useState('light');
  const [compactMode, setCompactMode] = useState(false);
  const [animations, setAnimations] = useState(true);
  
  // Analysis Preferences
  const [autoAnalyze, setAutoAnalyze] = useState(false);
  const [confidenceThreshold, setConfidenceThreshold] = useState('75');
  const [showAlternatives, setShowAlternatives] = useState(true);
  const [maxAlternatives, setMaxAlternatives] = useState('3');
  
  // Notifications
  const [emailNotifications, setEmailNotifications] = useState(false);
  const [analysisComplete, setAnalysisComplete] = useState(true);
  const [systemAlerts, setSystemAlerts] = useState(true);
  
  // Privacy
  const [anonymizeData, setAnonymizeData] = useState(false);
  const [shareAnalytics, setShareAnalytics] = useState(false);
  
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSaveSettings = () => {
    // In a real app, this would save to backend/localStorage
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Settings"
        description="Configure your KneeVision AI preferences and system settings"
      />

      {saveSuccess && (
        <Alert className="border-green-200 bg-green-50 dark:bg-green-950">
          <Info className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800 dark:text-green-200">
            Settings saved successfully! Changes will take effect immediately.
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="general" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2 lg:grid-cols-6">
          <TabsTrigger value="general" className="gap-2">
            <Settings2 className="h-4 w-4" />
            <span className="hidden sm:inline">General</span>
          </TabsTrigger>
          <TabsTrigger value="appearance" className="gap-2">
            <Palette className="h-4 w-4" />
            <span className="hidden sm:inline">Appearance</span>
          </TabsTrigger>
          <TabsTrigger value="analysis" className="gap-2">
            <Activity className="h-4 w-4" />
            <span className="hidden sm:inline">Analysis</span>
          </TabsTrigger>
          <TabsTrigger value="notifications" className="gap-2">
            <Bell className="h-4 w-4" />
            <span className="hidden sm:inline">Notifications</span>
          </TabsTrigger>
          <TabsTrigger value="privacy" className="gap-2">
            <Shield className="h-4 w-4" />
            <span className="hidden sm:inline">Privacy</span>
          </TabsTrigger>
          <TabsTrigger value="data" className="gap-2">
            <Database className="h-4 w-4" />
            <span className="hidden sm:inline">Data</span>
          </TabsTrigger>
        </TabsList>

        {/* General Settings */}
        <TabsContent value="general" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>General Settings</CardTitle>
              <CardDescription>Manage your basic application preferences</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="auto-save">Auto-save analysis results</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically save your analysis results as you work
                  </p>
                </div>
                <Switch
                  id="auto-save"
                  checked={autoSave}
                  onCheckedChange={setAutoSave}
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="tutorials">Show tutorials and tips</Label>
                  <p className="text-sm text-muted-foreground">
                    Display helpful guides for new features
                  </p>
                </div>
                <Switch
                  id="tutorials"
                  checked={showTutorials}
                  onCheckedChange={setShowTutorials}
                />
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>Default landing page</Label>
                <Select defaultValue="dashboard">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="dashboard">Dashboard</SelectItem>
                    <SelectItem value="implant-sizing">Implant Sizing</SelectItem>
                    <SelectItem value="medical-imaging">Medical Imaging</SelectItem>
                    <SelectItem value="oa-analytics">OA Analytics</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  Choose which page to show when you open the application
                </p>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>Language</Label>
                <Select defaultValue="en">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="es">Spanish</SelectItem>
                    <SelectItem value="fr">French</SelectItem>
                    <SelectItem value="de">German</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Appearance Settings */}
        <TabsContent value="appearance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Appearance Settings</CardTitle>
              <CardDescription>Customize the look and feel of your application</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>Theme</Label>
                <Select value={theme} onValueChange={setTheme}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">Light</SelectItem>
                    <SelectItem value="dark">Dark</SelectItem>
                    <SelectItem value="system">System</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  Choose your preferred color theme
                </p>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="compact-mode">Compact mode</Label>
                  <p className="text-sm text-muted-foreground">
                    Reduce spacing and padding for a denser layout
                  </p>
                </div>
                <Switch
                  id="compact-mode"
                  checked={compactMode}
                  onCheckedChange={setCompactMode}
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="animations">Enable animations</Label>
                  <p className="text-sm text-muted-foreground">
                    Show smooth transitions and animations
                  </p>
                </div>
                <Switch
                  id="animations"
                  checked={animations}
                  onCheckedChange={setAnimations}
                />
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>Font size</Label>
                <Select defaultValue="medium">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="small">Small</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="large">Large</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analysis Preferences */}
        <TabsContent value="analysis" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Analysis Preferences</CardTitle>
              <CardDescription>Configure AI analysis behavior and display options</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="auto-analyze">Auto-analyze on input</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically analyze when all required inputs are provided
                  </p>
                </div>
                <Switch
                  id="auto-analyze"
                  checked={autoAnalyze}
                  onCheckedChange={setAutoAnalyze}
                />
              </div>

              <Separator />

              <div className="space-y-2">
                <Label htmlFor="confidence-threshold">Minimum confidence threshold (%)</Label>
                <Input
                  id="confidence-threshold"
                  type="number"
                  min="0"
                  max="100"
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(e.target.value)}
                />
                <p className="text-sm text-muted-foreground">
                  Only show results with confidence above this threshold
                </p>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="show-alternatives">Show alternative recommendations</Label>
                  <p className="text-sm text-muted-foreground">
                    Display alternative implant options alongside the top recommendation
                  </p>
                </div>
                <Switch
                  id="show-alternatives"
                  checked={showAlternatives}
                  onCheckedChange={setShowAlternatives}
                />
              </div>

              {showAlternatives && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="max-alternatives">Maximum alternatives to show</Label>
                    <Select value={maxAlternatives} onValueChange={setMaxAlternatives}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">1</SelectItem>
                        <SelectItem value="2">2</SelectItem>
                        <SelectItem value="3">3</SelectItem>
                        <SelectItem value="5">5</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </>
              )}

              <Separator />

              <div className="space-y-2">
                <Label>Measurement units</Label>
                <Select defaultValue="mm">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="mm">Millimeters (mm)</SelectItem>
                    <SelectItem value="cm">Centimeters (cm)</SelectItem>
                    <SelectItem value="in">Inches (in)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>Manage how and when you receive notifications</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="email-notifications">Email notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive email updates about your analyses
                  </p>
                </div>
                <Switch
                  id="email-notifications"
                  checked={emailNotifications}
                  onCheckedChange={setEmailNotifications}
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="analysis-complete">Analysis completion alerts</Label>
                  <p className="text-sm text-muted-foreground">
                    Get notified when image analysis is complete
                  </p>
                </div>
                <Switch
                  id="analysis-complete"
                  checked={analysisComplete}
                  onCheckedChange={setAnalysisComplete}
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="system-alerts">System alerts</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive important system updates and maintenance notices
                  </p>
                </div>
                <Switch
                  id="system-alerts"
                  checked={systemAlerts}
                  onCheckedChange={setSystemAlerts}
                />
              </div>

              <Separator />

              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  Notification settings are stored locally and will be applied to this browser only.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Privacy Settings */}
        <TabsContent value="privacy" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Privacy & Security</CardTitle>
              <CardDescription>Control your data privacy and security preferences</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="anonymize">Anonymize patient data</Label>
                  <p className="text-sm text-muted-foreground">
                    Remove identifying information from exported reports
                  </p>
                </div>
                <Switch
                  id="anonymize"
                  checked={anonymizeData}
                  onCheckedChange={setAnonymizeData}
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="share-analytics">Share anonymous usage analytics</Label>
                  <p className="text-sm text-muted-foreground">
                    Help improve the application by sharing anonymous usage data
                  </p>
                </div>
                <Switch
                  id="share-analytics"
                  checked={shareAnalytics}
                  onCheckedChange={setShareAnalytics}
                />
              </div>

              <Separator />

              <Alert className="bg-blue-50 dark:bg-blue-950 border-blue-200">
                <Shield className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-800 dark:text-blue-200">
                  <strong>Data Protection:</strong> All patient data is processed securely and in compliance with 
                  healthcare data protection regulations. No personally identifiable information is shared without consent.
                </AlertDescription>
              </Alert>

              <div className="space-y-2">
                <Label>Session timeout</Label>
                <Select defaultValue="30">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="15">15 minutes</SelectItem>
                    <SelectItem value="30">30 minutes</SelectItem>
                    <SelectItem value="60">1 hour</SelectItem>
                    <SelectItem value="never">Never</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  Automatically log out after period of inactivity
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Data Management */}
        <TabsContent value="data" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Data Management</CardTitle>
              <CardDescription>Manage your stored data and application cache</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Cached analysis results</Label>
                    <p className="text-sm text-muted-foreground">
                      Locally stored analysis data for quick access
                    </p>
                  </div>
                  <Badge variant="outline">~2.5 MB</Badge>
                </div>
                <Button variant="outline" size="sm">
                  Clear Cache
                </Button>
              </div>

              <Separator />

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Uploaded images</Label>
                    <p className="text-sm text-muted-foreground">
                      Medical images stored for analysis
                    </p>
                  </div>
                  <Badge variant="outline">~15.3 MB</Badge>
                </div>
                <Button variant="outline" size="sm">
                  Manage Images
                </Button>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>Export format preference</Label>
                <Select defaultValue="pdf">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pdf">PDF</SelectItem>
                    <SelectItem value="json">JSON</SelectItem>
                    <SelectItem value="csv">CSV</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  Default format for exported analysis reports
                </p>
              </div>

              <Separator />

              <Alert variant="destructive">
                <AlertDescription>
                  <strong>Danger Zone:</strong> Clearing all data will permanently delete your local analysis history 
                  and uploaded images. This action cannot be undone.
                </AlertDescription>
              </Alert>
              <Button variant="destructive" size="sm">
                Clear All Data
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Save Button */}
      <div className="flex justify-end gap-3">
        <Button variant="outline">Reset to Defaults</Button>
        <Button onClick={handleSaveSettings} className="gap-2">
          <Save className="h-4 w-4" />
          Save Settings
        </Button>
      </div>
    </div>
  );
}

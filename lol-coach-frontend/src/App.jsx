import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { 
  Crown, 
  Headphones, 
  BarChart3, 
  Zap, 
  Shield, 
  Users, 
  CheckCircle2,
  ArrowRight,
  Menu,
  X,
  CreditCard,
  Smartphone
} from 'lucide-react'
import './App.css'

function App() {
  const [currentPage, setCurrentPage] = useState('home')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [user, setUser] = useState(null)

  // Componente de Navegação
  const Navigation = () => (
    <nav className="fixed top-0 w-full bg-slate-900/95 backdrop-blur-sm border-b border-slate-800 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setCurrentPage('home')}>
            <img src="/logo.png" alt="Pro Coach Virtual" className="h-10 w-10" />
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              Pro Coach Virtual
            </span>
          </div>
          
          {/* Desktop Menu */}
          <div className="hidden md:flex items-center gap-8">
            <button 
              onClick={() => setCurrentPage('home')}
              className="text-slate-300 hover:text-white transition-colors"
            >
              Início
            </button>
            <button 
              onClick={() => setCurrentPage('features')}
              className="text-slate-300 hover:text-white transition-colors"
            >
              Recursos
            </button>
            <button 
              onClick={() => setCurrentPage('pricing')}
              className="text-slate-300 hover:text-white transition-colors"
            >
              Preços
            </button>
            {isLoggedIn ? (
              <Button 
                onClick={() => setCurrentPage('dashboard')}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              >
                Dashboard
              </Button>
            ) : (
              <Button 
                onClick={() => setCurrentPage('login')}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              >
                Entrar
              </Button>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button 
            className="md:hidden text-white"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-slate-800 border-t border-slate-700">
          <div className="px-4 py-4 space-y-3">
            <button 
              onClick={() => { setCurrentPage('home'); setMobileMenuOpen(false); }}
              className="block w-full text-left text-slate-300 hover:text-white py-2"
            >
              Início
            </button>
            <button 
              onClick={() => { setCurrentPage('features'); setMobileMenuOpen(false); }}
              className="block w-full text-left text-slate-300 hover:text-white py-2"
            >
              Recursos
            </button>
            <button 
              onClick={() => { setCurrentPage('pricing'); setMobileMenuOpen(false); }}
              className="block w-full text-left text-slate-300 hover:text-white py-2"
            >
              Preços
            </button>
            <Button 
              onClick={() => { setCurrentPage('login'); setMobileMenuOpen(false); }}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600"
            >
              {isLoggedIn ? 'Dashboard' : 'Entrar'}
            </Button>
          </div>
        </div>
      )}
    </nav>
  )

  // Página Inicial
  const HomePage = () => (
    <div className="min-h-screen bg-slate-950">
      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-4 overflow-hidden">
        <div 
          className="absolute inset-0 opacity-40"
          style={{
            backgroundImage: 'url(/hero-banner-safe.png)',
            backgroundSize: 'cover',
            backgroundPosition: 'center'
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-slate-950/50 via-slate-950/80 to-slate-950" />
        
        <div className="relative max-w-7xl mx-auto text-center">
          <Badge className="mb-6 bg-blue-600/20 text-blue-400 border-blue-500/50">
            <Zap className="w-4 h-4 mr-2" />
            Coaching em Tempo Real
          </Badge>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent leading-tight">
            Eleve Seu Jogo ao<br />Próximo Nível
          </h1>
          
          <p className="text-xl md:text-2xl text-slate-300 mb-8 max-w-3xl mx-auto">
            Tenha seu coach virtual para te ajudar a subir de elo. Treinamento profissional com IA em tempo real, análises detalhadas e coaching por voz durante suas partidas.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button 
              size="lg"
              onClick={() => setCurrentPage('pricing')}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-lg px-8"
            >
              Começar Agora
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
            <Button 
              size="lg"
              variant="outline"
              onClick={() => setCurrentPage('features')}
              className="border-slate-600 text-slate-300 hover:bg-slate-800 text-lg px-8"
            >
              Ver Recursos
            </Button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-4 bg-slate-900/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-4 text-white">
            Recursos Poderosos
          </h2>
          <p className="text-center text-slate-400 mb-12 text-lg">
            Tudo que você precisa para dominar suas partidas
          </p>
          
          <div className="grid md:grid-cols-3 gap-8">
            <Card className="bg-slate-800/50 border-slate-700 hover:border-blue-500/50 transition-all hover:transform hover:scale-105">
              <CardHeader>
                <div className="w-12 h-12 bg-blue-600/20 rounded-lg flex items-center justify-center mb-4">
                  <Headphones className="w-6 h-6 text-blue-400" />
                </div>
                <CardTitle className="text-white">Coaching por Voz</CardTitle>
                <CardDescription className="text-slate-400">
                  Receba dicas e estratégias em tempo real através de áudio durante suas partidas
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700 hover:border-purple-500/50 transition-all hover:transform hover:scale-105">
              <CardHeader>
                <div className="w-12 h-12 bg-purple-600/20 rounded-lg flex items-center justify-center mb-4">
                  <BarChart3 className="w-6 h-6 text-purple-400" />
                </div>
                <CardTitle className="text-white">Análise Detalhada</CardTitle>
                <CardDescription className="text-slate-400">
                  Estatísticas completas, gráficos de desempenho e relatórios pós-partida
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700 hover:border-pink-500/50 transition-all hover:transform hover:scale-105">
              <CardHeader>
                <div className="w-12 h-12 bg-pink-600/20 rounded-lg flex items-center justify-center mb-4">
                  <Shield className="w-6 h-6 text-pink-400" />
                </div>
                <CardTitle className="text-white">100% Seguro</CardTitle>
                <CardDescription className="text-slate-400">
                  Totalmente compatível com as regras do jogo, sem risco de banimento
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-5xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">
                10K+
              </div>
              <div className="text-slate-400">Jogadores Ativos</div>
            </div>
            <div>
              <div className="text-5xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">
                85%
              </div>
              <div className="text-slate-400">Taxa de Melhoria</div>
            </div>
            <div>
              <div className="text-5xl font-bold bg-gradient-to-r from-pink-400 to-blue-400 bg-clip-text text-transparent mb-2">
                24/7
              </div>
              <div className="text-slate-400">Suporte Disponível</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-gradient-to-r from-blue-600/20 to-purple-600/20">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-6">
            Pronto para Começar?
          </h2>
          <p className="text-xl text-slate-300 mb-8">
            Junte-se a milhares de jogadores que já estão melhorando com o Pro Coach Virtual
          </p>
          <Button 
            size="lg"
            onClick={() => setCurrentPage('pricing')}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-lg px-12"
          >
            Ver Planos
            <Crown className="ml-2 w-5 h-5" />
          </Button>
        </div>
      </section>
    </div>
  )

  // Página de Preços
  const PricingPage = () => (
    <div className="min-h-screen bg-slate-950 pt-32 pb-20 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-white mb-4">
            Escolha Seu Plano
          </h1>
          <p className="text-xl text-slate-400">
            Todos os planos incluem acesso completo a todos os recursos
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {/* Plano Mensal */}
          <Card className="bg-slate-800/50 border-slate-700 hover:border-blue-500/50 transition-all">
            <CardHeader>
              <CardTitle className="text-2xl text-white">Mensal</CardTitle>
              <CardDescription className="text-slate-400">
                Perfeito para experimentar
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-6">
                <span className="text-5xl font-bold text-white">R$ 29,90</span>
                <span className="text-slate-400">/mês</span>
              </div>
              <ul className="space-y-3">
                <li className="flex items-center text-slate-300">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3" />
                  Coaching por voz em tempo real
                </li>
                <li className="flex items-center text-slate-300">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3" />
                  Análises detalhadas de partidas
                </li>
                <li className="flex items-center text-slate-300">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3" />
                  Suporte prioritário
                </li>
                <li className="flex items-center text-slate-300">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3" />
                  Atualizações automáticas
                </li>
              </ul>
            </CardContent>
            <CardFooter>
              <Button 
                className="w-full bg-blue-600 hover:bg-blue-700"
                onClick={() => setCurrentPage('checkout')}
              >
                Assinar Agora
              </Button>
            </CardFooter>
          </Card>

          {/* Plano Trimestral */}
          <Card className="bg-slate-800/50 border-purple-500 hover:border-purple-400 transition-all relative transform scale-105">
            <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-purple-600">
              Mais Popular
            </Badge>
            <CardHeader>
              <CardTitle className="text-2xl text-white">Trimestral</CardTitle>
              <CardDescription className="text-slate-400">
                Economize 10%
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-6">
                <span className="text-5xl font-bold text-white">R$ 80,73</span>
                <span className="text-slate-400">/3 meses</span>
                <div className="text-sm text-green-400 mt-1">R$ 26,91/mês</div>
              </div>
              <ul className="space-y-3">
                <li className="flex items-center text-slate-300">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3" />
                  Coaching por voz em tempo real
                </li>
                <li className="flex items-center text-slate-300">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3" />
                  Análises detalhadas de partidas
                </li>
                <li className="flex items-center text-slate-300">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3" />
                  Suporte prioritário
                </li>
                <li className="flex items-center text-slate-300">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3" />
                  Atualizações automáticas
                </li>
              </ul>
            </CardContent>
            <CardFooter>
              <Button 
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                onClick={() => setCurrentPage('checkout')}
              >
                Assinar Agora
              </Button>
            </CardFooter>
          </Card>

          {/* Plano Anual */}
          <Card className="bg-slate-800/50 border-slate-700 hover:border-pink-500/50 transition-all">
            <CardHeader>
              <CardTitle className="text-2xl text-white">Anual</CardTitle>
              <CardDescription className="text-slate-400">
                Melhor custo-benefício
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-6">
                <span className="text-5xl font-bold text-white">R$ 287,04</span>
                <span className="text-slate-400">/ano</span>
                <div className="text-sm text-green-400 mt-1">R$ 23,92/mês - Economize 20%</div>
              </div>
              <ul className="space-y-3">
                <li className="flex items-center text-slate-300">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3" />
                  Coaching por voz em tempo real
                </li>
                <li className="flex items-center text-slate-300">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3" />
                  Análises detalhadas de partidas
                </li>
                <li className="flex items-center text-slate-300">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3" />
                  Suporte prioritário
                </li>
                <li className="flex items-center text-slate-300">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3" />
                  Atualizações automáticas
                </li>
              </ul>
            </CardContent>
            <CardFooter>
              <Button 
                className="w-full bg-pink-600 hover:bg-pink-700"
                onClick={() => setCurrentPage('checkout')}
              >
                Assinar Agora
              </Button>
            </CardFooter>
          </Card>
        </div>

        {/* Payment Methods */}
        <div className="mt-16 text-center">
          <p className="text-slate-400 mb-6">Formas de pagamento aceitas:</p>
          <div className="flex justify-center gap-8 flex-wrap">
            <div className="flex items-center gap-2 text-slate-300">
              <Smartphone className="w-6 h-6 text-green-500" />
              <span>Pix</span>
            </div>
            <div className="flex items-center gap-2 text-slate-300">
              <CreditCard className="w-6 h-6 text-blue-500" />
              <span>Cartão de Crédito</span>
            </div>
            <div className="flex items-center gap-2 text-slate-300">
              <CreditCard className="w-6 h-6 text-purple-500" />
              <span>Cartão de Débito</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  // Página de Login/Registro
  const LoginPage = () => (
    <div className="min-h-screen bg-slate-950 pt-32 pb-20 px-4">
      <div className="max-w-md mx-auto">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-2xl text-white text-center">Bem-vindo</CardTitle>
            <CardDescription className="text-center">
              Entre ou crie sua conta para começar
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="login" className="w-full">
              <TabsList className="grid w-full grid-cols-2 mb-6">
                <TabsTrigger value="login">Entrar</TabsTrigger>
                <TabsTrigger value="register">Registrar</TabsTrigger>
              </TabsList>
              
              <TabsContent value="login">
                <form className="space-y-4">
                  <div>
                    <Label htmlFor="username">Usuário</Label>
                    <Input 
                      id="username" 
                      placeholder="Seu nome de usuário"
                      className="bg-slate-900 border-slate-700"
                    />
                  </div>
                  <div>
                    <Label htmlFor="password">Senha</Label>
                    <Input 
                      id="password" 
                      type="password"
                      placeholder="Sua senha"
                      className="bg-slate-900 border-slate-700"
                    />
                  </div>
                  <Button 
                    type="submit"
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600"
                  >
                    Entrar
                  </Button>
                </form>
              </TabsContent>
              
              <TabsContent value="register">
                <form className="space-y-4">
                  <div>
                    <Label htmlFor="new-username">Usuário</Label>
                    <Input 
                      id="new-username" 
                      placeholder="Escolha um nome de usuário"
                      className="bg-slate-900 border-slate-700"
                    />
                  </div>
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input 
                      id="email" 
                      type="email"
                      placeholder="seu@email.com"
                      className="bg-slate-900 border-slate-700"
                    />
                  </div>
                  <div>
                    <Label htmlFor="new-password">Senha</Label>
                    <Input 
                      id="new-password" 
                      type="password"
                      placeholder="Crie uma senha forte"
                      className="bg-slate-900 border-slate-700"
                    />
                  </div>
                  <Button 
                    type="submit"
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600"
                  >
                    Criar Conta
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  )

  // Renderização condicional de páginas
  const renderPage = () => {
    switch(currentPage) {
      case 'home':
        return <HomePage />
      case 'pricing':
        return <PricingPage />
      case 'login':
        return <LoginPage />
      default:
        return <HomePage />
    }
  }

  return (
    <div className="min-h-screen bg-slate-950">
      <Navigation />
      {renderPage()}
      
      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 py-12 px-4">
        <div className="max-w-7xl mx-auto text-center text-slate-400">
          <p className="mb-2">© 2024 Pro Coach Virtual. Todos os direitos reservados.</p>
          <p className="text-sm">
            Pro Coach Virtual não é endossado pela Riot Games e não reflete as opiniões ou visões da Riot Games ou de qualquer pessoa oficialmente envolvida na produção ou gerenciamento de League of Legends.
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
